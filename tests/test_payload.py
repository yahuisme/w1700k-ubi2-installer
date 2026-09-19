import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('fetch', Path(__file__).parents[1] / 'scripts/fetch-firmware.py')
assert spec is not None and spec.loader is not None
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


class PayloadTests(unittest.TestCase):
    def release(self):
        tag = 'W1700K-OpenWrt-r36377-26.09.19-12.31.37'
        data = bytes.fromhex('d00dfeed') + b'fixture'
        return {'tag_name': tag, 'draft': False, 'prerelease': False, 'assets': [{
            'name': fetch.IMAGE, 'size': len(data),
            'digest': 'sha256:' + hashlib.sha256(data).hexdigest(),
            'browser_download_url': f'https://github.com/{fetch.REPOSITORY}/releases/download/{tag}/{fetch.IMAGE}'}]}, data

    def test_valid(self):
        release, data = self.release()
        asset = fetch.select_asset(release)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'image'; p.write_bytes(data)
            fetch.verify_file(p, asset)
            p.write_bytes(data[:-1] + b'x')
            with self.assertRaises(ValueError): fetch.verify_file(p, asset)
            p.write_bytes(data[:-1])
            with self.assertRaises(ValueError): fetch.verify_file(p, asset)

    def test_wrong_release(self):
        for key, value in [('tag_name', 'W1700K-OpenWrt-OC-r1-26.09.19-12.00.00'), ('draft', True), ('prerelease', True)]:
            r, _ = self.release(); r[key] = value
            with self.assertRaises(ValueError): fetch.select_asset(r)

    def test_assets(self):
        for mode in ['missing', 'duplicate', 'digest', 'url', 'size']:
            r, _ = self.release()
            if mode == 'missing': r['assets'] = []
            elif mode == 'duplicate': r['assets'] *= 2
            elif mode == 'digest': r['assets'][0]['digest'] = None
            elif mode == 'url': r['assets'][0]['browser_download_url'] = 'https://example.com/image'
            else: r['assets'][0]['size'] = 0
            with self.assertRaises(ValueError): fetch.select_asset(r)


if __name__ == '__main__':
    unittest.main()
