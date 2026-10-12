import copy
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release', Path(__file__).parents[1] / 'scripts/verify-release.py')
assert spec and spec.loader
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def test_publication_gate(self):
        with tempfile.TemporaryDirectory(prefix='installer-release-') as d:
            directory = Path(d)
            names = ['installer.itb', 'chainloader.itb']
            assets = []
            for name in names:
                (directory / name).write_bytes(name.encode())
                assets.append(dict(name=name, size=len(name), state='uploaded', url='https://api.github.com/fixture', digest='sha256:' + hashlib.sha256(name.encode()).hexdigest()))
            good = dict(draft=False, prerelease=False, assets=assets)
            release.verify(good, directory, names)
            for defect in ['draft', 'prerelease', 'missing', 'extra', 'size', 'state', 'digest']:
                bad = copy.deepcopy(good)
                if defect in ['draft', 'prerelease']: bad[defect] = True
                elif defect == 'missing': bad['assets'].pop()
                elif defect == 'extra': bad['assets'].append(bad['assets'][0])
                elif defect == 'size': bad['assets'][0]['size'] = 0
                elif defect == 'state': bad['assets'][0]['state'] = 'starter'
                else: bad['assets'][0]['digest'] = 'sha256:' + '0' * 64
                with self.subTest(defect=defect), self.assertRaises(ValueError):
                    release.verify(bad, directory, names)
            no_digest = copy.deepcopy(good)
            for asset in no_digest['assets']: asset['digest'] = None
            for mode in ['good', 'corrupt', 'exit']:
                index = [0]
                def download(args, stdout, check):
                    data = names[index[0]].encode(); index[0] += 1
                    stdout.write(data if mode != 'corrupt' else b'bad')
                    if mode == 'exit': raise subprocess.CalledProcessError(1, args)
                with self.subTest(fallback=mode), patch.object(release.subprocess, 'run', side_effect=download):
                    if mode == 'good': release.verify(no_digest, directory, names)
                    else:
                        with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                            release.verify(no_digest, directory, names)


if __name__ == '__main__':
    unittest.main()
