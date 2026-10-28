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

    def test_existing_release_cannot_be_overwritten_on_rerun(self):
        steps = [step for step in WORKFLOW['jobs']['build']['steps']
                 if step['name'] == 'Check installer release tag']
        command = steps[0]['run'] if steps else ':'
        for mode in ['existing', 'draft', 'prerelease', 'new', 'api-failure', 'invalid-json', 'invalid-shape']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix='installer-tag-') as d:
                p = Path(d)
                shutil.copytree(ROOT / 'scripts', p / 'installer-repo/scripts')
                stub = p / 'stub'; stub.mkdir()
                gh = stub / 'gh'
                inventory = [[dict(tag_name=f'other-{n}') for n in range(100)], []]
                if mode in ['existing', 'draft', 'prerelease']:
                    inventory[1].append(dict(tag_name='ubi2-installer-8',
                                             draft=mode == 'draft', prerelease=mode == 'prerelease'))
                if mode == 'invalid-shape': inventory = {}
                (p / 'inventory.json').write_text('invalid' if mode == 'invalid-json' else json.dumps(inventory))
                gh.write_text('''#!/bin/sh
[ "$1 $2 $3" = "api --paginate --slurp" ] || exit 99
[ "$MODE" != api-failure ] || exit 7
cat "$AUDIT_ROOT/inventory.json"
''')
                gh.chmod(0o755)
                env = dict(os.environ, GITHUB_REPOSITORY='fixture/installer',
                           GITHUB_RUN_NUMBER='8', MODE=mode, AUDIT_ROOT=str(p))
                env['PATH'] = str(stub) + ':' + env['PATH']
                result = subprocess.run(['bash', '-euo', 'pipefail', '-c', command],
                                        cwd=p, env=env, capture_output=True, text=True)
                if mode == 'new':
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0, result.stderr)
                    if mode in ['existing', 'draft', 'prerelease']:
                        self.assertIn('already exists', result.stderr)
        release = next(s for s in WORKFLOW['jobs']['build']['steps']
                       if s['name'] == 'Create new GitHub Release')
        self.assertFalse(release['with']['overwrite_files'])
        if steps:
            names = [step['name'] for step in WORKFLOW['jobs']['build']['steps']]
            self.assertLess(names.index('Check installer release tag'), names.index('Fetch latest OpenWrt payload'))

    def test_builds_are_serialized(self):
        self.assertEqual(WORKFLOW['concurrency'], {'group': 'w1700k-installer-release', 'cancel-in-progress': False})

    def test_cleanup_only_after_exact_publication(self):
        for defect in ['', 'draft', 'prerelease', 'digest', 'missing', 'state', 'tag',
                       'list-failure', 'missing-current', 'invalid-inventory', 'invalid-state',
                       'empty-inventory', 'delete-failure', 'no-previous']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory(prefix='installer-cleanup-') as d:
                p = Path(d)
                shutil.copytree(ROOT / 'scripts', p / 'installer-repo/scripts')
                out = p / 'output/installer'; out.mkdir(parents=True)
                env = dict(os.environ, **WORKFLOW['env'], GITHUB_REPOSITORY='fixture/installer', GITHUB_RUN_NUMBER='8', AUDIT_ROOT=str(p))
                assets = []
                for key in ['INSTALLER_IMAGE', 'UBOOT_IMAGE']:
                    name = env[key]; (out / name).write_bytes(name.encode())
                    assets.append(dict(name=name, size=len(name), state='uploaded', digest='sha256:' + hashlib.sha256(name.encode()).hexdigest()))
                release = dict(tag_name='ubi2-installer-8', draft=defect == 'draft', prerelease=defect == 'prerelease', assets=assets)
                if defect == 'tag': release['tag_name'] = 'ubi2-installer-7'
                if defect == 'digest': assets[0]['digest'] = 'sha256:' + '0' * 64
                if defect == 'missing': assets.pop()
                if defect == 'state': assets[0]['state'] = 'starter'
                (p / 'release.json').write_text(json.dumps(release))
                stub = p / 'stub'; stub.mkdir()
                gh = stub / 'gh'
                inventory = [dict(tag_name=tag, draft=draft, prerelease=pre) for tag, draft, pre in [
                    ('ubi2-installer-9', False, False), ('ubi2-installer-8', False, False),
                    ('ubi2-installer-7', False, False), ('ubi2-installer-6', True, False),
                    ('ubi2-installer-5', False, True), ('ubi2-installer-beta', False, False),
                    ('other-release', False, False), ('ubi2-installer-08', False, False),
                ]]
                if defect == 'missing-current':
                    inventory = [r for r in inventory if r['tag_name'] != 'ubi2-installer-8']
                if defect == 'no-previous':
                    inventory = [r for r in inventory if r['tag_name'] != 'ubi2-installer-7']
                if defect == 'invalid-state':
                    inventory[-1]['draft'] = 'false'
                pages = [[dict(tag_name=f'other-{n}', draft=False, prerelease=False)
                          for n in range(100)], inventory]
                if defect == 'empty-inventory': pages = [[]]
                (p / 'inventory.json').write_text('not-json' if defect == 'invalid-inventory' else json.dumps(pages))
                env['DEFECT'] = defect
                gh.write_text('''#!/bin/sh
case "$1 $2" in
"api repos/fixture/installer/releases/tags/ubi2-installer-8") cat "$AUDIT_ROOT/release.json";;
"api --paginate")
  [ "$DEFECT" != list-failure ] || exit 7
  cat "$AUDIT_ROOT/inventory.json";;
"release delete")
  [ "$DEFECT" != delete-failure ] || exit 8
  printf "%s\\n" "$3" >> "$AUDIT_ROOT/deleted";;
*) exit 99;;
esac
''')
                gh.chmod(0o755); env['PATH'] = str(stub) + ':' + env['PATH']
                r = subprocess.run(['bash', '-euo', 'pipefail', '-c', block('Remove previous')], cwd=p, env=env, capture_output=True, text=True)
                if defect == 'no-previous':
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertFalse((p / 'deleted').exists())
                elif defect:
                    self.assertNotEqual(r.returncode, 0, r.stderr)
                    self.assertFalse((p / 'deleted').exists())
                else:
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertEqual((p / 'deleted').read_text(), 'ubi2-installer-7\n')


if __name__ == '__main__':
    unittest.main()
