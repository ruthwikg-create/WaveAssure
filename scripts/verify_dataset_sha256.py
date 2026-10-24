"""Verify downloaded VTaC files against PhysioNet's official SHA256SUMS.txt.

A valid WFDB additive checksum catches some corruption, but cannot establish
provenance. Use a *version-matched* PhysioNet manifest to test file authenticity.
No network requests are made and no files are modified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

SHA256 = re.compile(r'^[0-9a-fA-F]{64}$')


def parse_manifest(path: Path) -> list[tuple[str, Path]]:
    rows = []
    for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or not SHA256.fullmatch(fields[0]):
            raise ValueError(f'Bad SHA256SUMS format on line {lineno}')
        name = fields[1].strip().lstrip('*')
        rel = Path(name.replace('\\', '/'))
        if rel.is_absolute() or not name or any(part in {'.', '..', ''} for part in rel.parts):
            raise ValueError(f'Unsafe manifest entry on line {lineno}')
        rows.append((fields[0].lower(), rel))
    if not rows:
        raise ValueError('Empty SHA256SUMS manifest')
    if len({str(rel) for _, rel in rows}) != len(rows):
        raise ValueError('Duplicate filename in SHA256SUMS manifest')
    return rows


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(root: Path, manifest: Path, *, only_existing: bool = True) -> dict:
    root = root.resolve(strict=True)
    stats = {'matching': 0, 'mismatching': 0, 'missing': 0, 'checked': 0, 'manifest_entries': 0}
    failed = []
    items = parse_manifest(manifest)
    stats['manifest_entries'] = len(items)
    for expected, relative in items:
        dest = (root / relative).resolve()
        if not dest.is_relative_to(root):
            raise ValueError('Manifest entry resolves outside dataset root')
        if not dest.is_file():
            stats['missing'] += 1
            if not only_existing:
                failed.append({'path': str(relative), 'status': 'MISSING'})
            continue
        stats['checked'] += 1
        if file_digest(dest) == expected:
            stats['matching'] += 1
        else:
            stats['mismatching'] += 1
            failed.append({'path': str(relative), 'status': 'SHA256_MISMATCH'})
    stats['ok_for_checked_files'] = stats['checked'] > 0 and stats['mismatching'] == 0
    stats['complete_manifest'] = stats['missing'] == 0 and stats['mismatching'] == 0
    stats['failures'] = failed[:100]
    stats['warning'] = ('Use only the SHA256SUMS.txt from the SAME PhysioNet release as your downloads. '
                        'Partial-manifest success does not establish dataset completeness or clinical validity.')
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', required=True, type=Path)
    ap.add_argument('--manifest', required=True, type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = verify(args.root, args.manifest)
    report = json.dumps(result, indent=2)
    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + '\n', encoding='utf-8')
    return 0 if result['ok_for_checked_files'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
