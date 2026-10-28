#!/usr/bin/env python3
"""Refuse to reuse an existing installer release on a workflow rerun."""
import json
import os
import subprocess


def main():
    repository = os.environ['GITHUB_REPOSITORY']
    tag = 'ubi2-installer-' + os.environ['GITHUB_RUN_NUMBER']
    pages = json.loads(subprocess.check_output([
        'gh', 'api', '--paginate', '--slurp',
        f'repos/{repository}/releases?per_page=100']))
    if not isinstance(pages, list) or not pages or any(not isinstance(page, list) for page in pages):
        raise ValueError('Invalid release inventory')
    if any(release['tag_name'] == tag for page in pages for release in page):
        raise SystemExit(f'Release {tag} already exists; start a new workflow run instead of rerunning it')
    print(f'Installer release tag is available: {tag}')


if __name__ == '__main__':
    main()
