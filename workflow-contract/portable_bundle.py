#!/usr/bin/env python3
"""Explicit-file transport only; never extracts, merges, or certifies research."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or str(p) != name:
        raise ValueError('Unsafe/noncanonical relative path: ' + name)
    if any(x.startswith('.') for x in p.parts) or any(
        word in p.name.lower() for word in ('cookie', 'credential', 'token', 'secret', 'private_key')
    ) or p.suffix.lower() in ('.pem', '.key'):
        raise ValueError('Excluded credential/hidden path: ' + name)
    return p


def identity(meta):
    return digest(json.dumps(meta, sort_keys=True, ensure_ascii=False).encode())


def pack(root, names, request, out, base_id=None):
    root = Path(root).resolve(strict=True)
    out = Path(out).resolve()
    if out.is_relative_to(root):
        raise ValueError('Output must be outside the project')
    if not names or len(names) != len(set(names)):
        raise ValueError('File list must be nonempty and unique')
    blobs = {}
    for name in sorted(names):
        safe_name(name)
        path = root / name
        if any(p.is_symlink() for p in [path, *path.parents] if p != root and p.is_relative_to(root)):
            raise ValueError('Symlinks are not portable: ' + name)
        if not path.resolve(strict=True).is_relative_to(root) or not path.is_file():
            raise ValueError('Not a project file: ' + name)
        blobs['project/' + name] = path.read_bytes()
    blobs['NEXT.md'] = request.encode('utf-8')
    if not request.strip():
        raise ValueError('A continuation request is required')
    meta = {'format': 1, 'base_id': base_id, 'files': {
        name: {'sha256': digest(data), 'size': len(data)} for name, data in blobs.items()}}
    meta['bundle_id'] = identity(meta)
    # Exclusive creation prevents accidental replacement of previous deliveries.
    with out.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, data in blobs.items():
                z.writestr(name, data)
            z.writestr('bundle.json', json.dumps(meta, ensure_ascii=False, indent=2))
    return meta


def verify(archive, expected_base=None):
    with zipfile.ZipFile(archive) as z:
        members = z.namelist()
        if len(members) != len(set(members)):
            raise ValueError('Duplicate ZIP members')
        meta = json.loads(z.read('bundle.json'))
        if meta.get('format') != 1:
            raise ValueError('Unsupported bundle format')
        claimed = meta.pop('bundle_id')
        if identity(meta) != claimed:
            raise ValueError('Manifest fingerprint mismatch')
        meta['bundle_id'] = claimed
        if expected_base is not None and meta['base_id'] != expected_base:
            raise ValueError('Return bundle is based on a different input')
        if set(members) != set(meta['files']) | {'bundle.json'} or 'NEXT.md' not in members:
            raise ValueError('Inventory mismatch')
        for name, info in meta['files'].items():
            if name != 'NEXT.md':
                if not name.startswith('project/'):
                    raise ValueError('Unexpected member')
                safe_name(name[len('project/'):])
            h = hashlib.sha256()
            size = 0
            with z.open(name) as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b''):
                    size += len(chunk)
                    h.update(chunk)
            if size != info['size'] or h.hexdigest() != info['sha256']:
                raise ValueError('File fingerprint mismatch: ' + name)
        return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('pack')
    p.add_argument('project')
    p.add_argument('--files', required=True)
    p.add_argument('--request', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--base-id')
    v = sub.add_parser('verify')
    v.add_argument('archive')
    v.add_argument('--expected-base')
    a = parser.parse_args()
    if a.command == 'pack':
        names = [x for x in Path(a.files).read_text(encoding='utf-8').splitlines() if x]
        meta = pack(a.project, names, Path(a.request).read_text(encoding='utf-8'), a.out, a.base_id)
    else:
        meta = verify(a.archive, a.expected_base)
    print(json.dumps({'bundle_id': meta['bundle_id'], 'base_id': meta['base_id'],
                      'file_count': len(meta['files']) - 1, 'transport_check': 'PASS',
                      'scientific_readiness': 'NOT_ASSESSED'}, ensure_ascii=False))

if __name__ == '__main__':
    main()
