#!/usr/bin/env python3
"""Remove older production installer releases after publication verification."""
import json
import os
import re
import subprocess


def main():
    repository = os.environ['GITHUB_REPOSITORY']
    run = os.environ['GITHUB_RUN_NUMBER']
    if not re.fullmatch(r'[1-9][0-9]*', run):
        raise ValueError('Invalid installer run number')
    current = f'ubi2-installer-{run}'
    pages = json.loads(subprocess.check_output([
        'gh', 'api', '--paginate', '--slurp',
        f'repos/{repository}/releases?per_page=100']))
    releases = [release for page in pages for release in page]
    # Parse the entire inventory before deleting anything.
    previous = []
    found = False
    for release in releases:
        tag = release['tag_name']
        draft, prerelease = release['draft'], release['prerelease']
        if not isinstance(draft, bool) or not isinstance(prerelease, bool):
            raise ValueError('Invalid release publication state')
        if draft or prerelease:
            continue
        if tag == current:
            found = True
        match = re.fullmatch(r'ubi2-installer-([1-9][0-9]*)', tag)
        if match and int(match[1]) < int(run):
            previous.append(tag)
    if not found:
        raise ValueError('Current installer release missing from inventory')
    for tag in previous:
        subprocess.run(['gh', 'release', 'delete', tag, '--repo', repository,
                        '--cleanup-tag', '--yes'], check=True)


if __name__ == '__main__':
    main()
