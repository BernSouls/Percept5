"""Restore only the 136 pinned ETH-80 images needed for the joint matrix.

Downloads the exact pinned source archive if it is not already cached; verifies
both its SHA-256 and every extracted image. Never rewrites the input manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = 'https://codeload.github.com/chenchkx/ETH-80/tar.gz/9243466b9ca5f15765c88fdaf17c4f10c15a8574'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='use an existing pinned source archive instead of downloading')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'phase3/inputs/eth80_all8.json').read_text())
    archive = args.archive or ROOT/'.cache/eth80/source.tar.gz'
    if not archive.is_file():
        if args.archive:
            raise FileNotFoundError(archive)
        archive.parent.mkdir(parents=True, exist_ok=True)
        temporary = archive.with_suffix('.download')
        print('Downloading pinned ETH-80 archive (~307 MB); this can take several minutes.', flush=True)
        try:
            urllib.request.urlretrieve(URL, temporary)
            if digest(temporary) != manifest['archive_sha256']:
                raise ValueError('downloaded archive SHA-256 mismatch')
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    if digest(archive) != manifest['archive_sha256']:
        raise ValueError(f'archive SHA-256 mismatch: {archive}')
    records = list(manifest['references'].values()) + [r for group in manifest['eval'].values() for r in group]
    if len(records) != 136:
        raise ValueError('expected 136 pinned references and held-out images')
    with tarfile.open(archive, 'r:gz') as tar:
        members = {}
        for member in tar:
            if member.isfile() and '/' in member.name:
                rel = member.name.split('/', 1)[1]
                if rel in members:
                    raise ValueError(f'duplicate archive member: {rel}')
                members[rel] = member
        for rec in records:
            member = members.get(rec['source_path'])
            if member is None:
                raise ValueError(f'missing archive member: {rec["source_path"]}')
            with tar.extractfile(member) as stream:
                content = stream.read()
            if hashlib.sha256(content).hexdigest() != rec['sha256']:
                raise ValueError(f'image SHA-256 mismatch: {rec["source_path"]}')
            dest = (ROOT/rec['path']).resolve()
            if not dest.is_relative_to((ROOT/'data/ETH-80').resolve()):
                raise ValueError(f'unsafe manifest destination: {dest}')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
    print(f'Restored and verified {len(records)} images; archive SHA-256 {manifest["archive_sha256"]}')


if __name__ == '__main__':
    main()
