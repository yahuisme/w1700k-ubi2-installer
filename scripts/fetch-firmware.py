#!/usr/bin/env python3
"""Download the latest standard W1700K OpenWrt release payload."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

REPOSITORY = 'yahuisme/w1700k-openwrt'
IMAGE = 'openwrt-airoha-an7581-gemtek_w1700k-ubi-squashfs-sysupgrade.itb'
HASH_CHUNK_SIZE = 1024 * 1024


def select_asset(release):
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Expected a published stable release')
    tag = release['tag_name']
    if not re.fullmatch(r'W1700K-OpenWrt-r[0-9]+-[0-9.]+-[0-9.]+', tag):
        raise ValueError('Expected a standard W1700K OpenWrt release')
    assets = [a for a in release['assets'] if a['name'] == IMAGE]
    if len(assets) != 1:
        raise ValueError('Expected exactly one board-specific sysupgrade image')
    asset = assets[0]
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', asset.get('digest') or ''):
        raise ValueError('Missing release SHA-256')
    if not isinstance(asset['size'], int) or asset['size'] <= 0:
        raise ValueError('Invalid image size')
    expected = f'https://github.com/{REPOSITORY}/releases/download/{tag}/{IMAGE}'
    if asset['browser_download_url'] != expected:
        raise ValueError('Unexpected download URL')
    return asset


def verify_file(path, asset):
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as source:
        while chunk := source.read(HASH_CHUNK_SIZE):
            digest.update(chunk)
            size += len(chunk)
    if size != asset['size']:
        raise ValueError('Image size mismatch')
    if 'sha256:' + digest.hexdigest() != asset['digest']:
        raise ValueError('Image SHA-256 mismatch')
    with path.open('rb') as source:
        if source.read(4) != bytes.fromhex('d00dfeed'):
            raise ValueError('Image is not FIT')


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f'usage: {sys.argv[0]} DESTINATION')
    destination = Path(sys.argv[1])
    release = json.loads(subprocess.check_output(
        ['gh', 'api', f'repos/{REPOSITORY}/releases/latest']))
    asset = select_asset(release)
    destination.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.payload-', dir=destination)
    os.close(fd)
    temporary = Path(temporary)
    try:
        subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                        '--retry', '3', '--retry-delay', '2',
                        '--connect-timeout', '15', '--max-time', '900',
                        '--proto', '=https', '--proto-redir', '=https',
                        '--output', str(temporary), asset['browser_download_url']], check=True)
        verify_file(temporary, asset)
        temporary.replace(destination / IMAGE)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Verified {release['tag_name']}: {asset['digest']}")
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f"tag={release['tag_name']}\nsha256={asset['digest'][7:]}\n")


if __name__ == '__main__':
    main()
