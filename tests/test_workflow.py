"""Exercise actual workflow staging and cleanup shell without network/builds."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((ROOT / '.github/workflows/w1700k.yaml').read_text())


def block(prefix):
    text = next(s['run'] for s in WORKFLOW['jobs']['build']['steps'] if s['name'].startswith(prefix))
    return re.sub(r'\$\{\{ env\.(\w+) \}\}', lambda m: '${' + m[1] + '}', text)


class WorkflowTests(unittest.TestCase):
    def test_stage_inner_recovery_and_payload(self):
        with tempfile.TemporaryDirectory(prefix='installer-stage-') as d:
            p = Path(d)
            shutil.copytree(ROOT / 'files', p / 'installer-repo/files')
            env = dict(os.environ, **WORKFLOW['env'])
            binary = p / 'openwrt/bin/targets/airoha/an7581'
            binary.mkdir(parents=True)
            (binary / env['RECOVERY_IMAGE']).write_bytes(b'inner-recovery')
            (p / 'installer-repo/files/installer' / env['SYSUPGRADE_IMAGE']).write_bytes(b'sysupgrade')
            tool = p / 'openwrt/staging_dir/host/bin/fwtool'
            tool.parent.mkdir(parents=True)
            metadata = dict(new_supported_devices=['gemtek,w1700k-ubi'], compat_version='2.0', version=dict(target='airoha/an7581', board='gemtek_w1700k-ubi'))
            tool.write_text('#!/bin/sh\nprintf \'%s\' \'' + json.dumps(metadata) + '\' > "$2"\n')
            tool.chmod(0o755)
            r = subprocess.run(['bash', '-euo', 'pipefail', '-c', block('Stage installer')], cwd=p, env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            staged = p / 'openwrt/files/installer'
            self.assertEqual((staged / env['RECOVERY_IMAGE']).read_bytes(), b'inner-recovery')
            self.assertFalse((staged / 'SHA256SUMS').exists())
            for relative in ('installer/install.sh', 'lib/preinit/00_installer'):
                self.assertEqual((p / 'openwrt/files' / relative).read_bytes(),
                                 (ROOT / 'files' / relative).read_bytes())
            (binary / env['RECOVERY_IMAGE']).write_bytes(b'outer-installer')
            self.assertEqual((staged / env['RECOVERY_IMAGE']).read_bytes(), b'inner-recovery')

    def test_cleanup_only_after_exact_publication(self):
        for defect in ['', 'draft', 'digest', 'missing', 'state']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory(prefix='installer-cleanup-') as d:
                p = Path(d)
                shutil.copytree(ROOT / 'scripts', p / 'installer-repo/scripts')
                out = p / 'output/installer'; out.mkdir(parents=True)
                env = dict(os.environ, **WORKFLOW['env'], GITHUB_REPOSITORY='fixture/installer', GITHUB_RUN_NUMBER='8', AUDIT_ROOT=str(p))
                assets = []
                for key in ['INSTALLER_IMAGE', 'UBOOT_IMAGE']:
                    name = env[key]; (out / name).write_bytes(name.encode())
                    assets.append(dict(name=name, size=len(name), state='uploaded', digest='sha256:' + hashlib.sha256(name.encode()).hexdigest()))
                release = dict(tag_name='ubi2-installer-8', draft=defect == 'draft', prerelease=False, assets=assets)
                if defect == 'digest': assets[0]['digest'] = 'sha256:' + '0' * 64
                if defect == 'missing': assets.pop()
                if defect == 'state': assets[0]['state'] = 'starter'
                (p / 'release.json').write_text(json.dumps(release))
                stub = p / 'stub'; stub.mkdir()
                gh = stub / 'gh'
                gh.write_text('#!/bin/sh\ncase "$1 $2" in\n"api repos/fixture/installer/releases/tags/ubi2-installer-8") cat "$AUDIT_ROOT/release.json";;\n"release list") printf "%s\\n" ubi2-installer-8 ubi2-installer-7 ubi2-installer-beta other-release;;\n"release delete") printf "%s\\n" "$3" >> "$AUDIT_ROOT/deleted";;\n*) exit 99;;\nesac\n')
                gh.chmod(0o755); env['PATH'] = str(stub) + ':' + env['PATH']
                r = subprocess.run(['bash', '-euo', 'pipefail', '-c', block('Remove previous')], cwd=p, env=env, capture_output=True, text=True)
                if defect:
                    self.assertNotEqual(r.returncode, 0)
                    self.assertFalse((p / 'deleted').exists())
                else:
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertEqual((p / 'deleted').read_text(), 'ubi2-installer-7\n')


if __name__ == '__main__':
    unittest.main()
