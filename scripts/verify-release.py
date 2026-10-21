#!/usr/bin/env python3
"""Confirm published installer bytes before allowing retention cleanup."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def verify(release, directory, names):
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Installer release is not published stable')
    assets = release['assets']
    if sorted(a['name'] for a in assets) != sorted(names):
        raise ValueError('Unexpected installer asset set')
    for asset in assets:
        local = directory / asset['name']
        if not local.is_file():
            raise ValueError('Missing local installer asset')
        if asset.get('state') != 'uploaded' or asset['size'] != local.stat().st_size or not asset['size']:
            raise ValueError('Incomplete installer upload')
        with local.open('rb') as source:
            digest = 'sha256:' + hashlib.file_digest(source, 'sha256').hexdigest()
        if asset.get('digest'):
            if asset['digest'] != digest:
                raise ValueError('Uploaded installer digest mismatch')
        else:
            # Older API responses can omit digest; verify downloaded bytes instead.
            with tempfile.TemporaryFile() as output:
                subprocess.run(['gh', 'api', asset['url'], '-H',
                                'Accept: application/octet-stream'], stdout=output, check=True)
                output.seek(0)
                remote_digest = hashlib.file_digest(output, 'sha256').hexdigest()
            if 'sha256:' + remote_digest != digest:
                raise ValueError('Downloaded installer digest mismatch')


def main():
    tag = 'ubi2-installer-' + os.environ['GITHUB_RUN_NUMBER']
    release = json.loads(subprocess.check_output([
        'gh', 'api', f"repos/{os.environ['GITHUB_REPOSITORY']}/releases/tags/{tag}"]))
    if release['tag_name'] != tag:
        raise ValueError('Unexpected release tag')
    verify(release, Path(sys.argv[1]), [os.environ['INSTALLER_IMAGE'], os.environ['UBOOT_IMAGE']])
    print(f'Confirmed published installer assets: {tag}')


if __name__ == '__main__':
    main()
