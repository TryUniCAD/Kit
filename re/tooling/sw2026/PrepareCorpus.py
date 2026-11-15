from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))

from convert.adapters.solidworks.container.Container import BuildSldprt, SldprtArchive

TEXT = re.compile(rb'(?:[ -~]\x00){4,}|[ -~]{4,}')


def redact(data, names):
    def replace(match):
        raw = match.group()
        codec = 'utf-16-le' if b'\0' in raw else 'ascii'
        text = raw.decode(codec)
        text = re.sub(
            r'(?:[A-Za-z]:[\\/]Users[\\/]|\\\\Mac\\Home\\|/Users/)[^<>"\r\n]*',
            lambda found: ('C:\\KitOracle\\' + '_' * len(found.group()))[:len(found.group())],
            text,
        )
        for name in names:
            text = re.sub(r'\b' + re.escape(name) + r'\b', '_' * len(name), text, flags=re.IGNORECASE)
        return text.encode(codec)
    return TEXT.sub(replace, data)


def main():
    parser = argparse.ArgumentParser(description='Prepare privacy-redacted research controls, never writer output')
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--redact-name', action='append', default=[])
    parser.add_argument('--kind', choices=('part', 'assembly'), default='part')
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    assembly = args.kind == 'assembly'
    manifest_name = 'manifest.json' if assembly else 'ladder.manifest.json'
    source_manifest = json.loads((args.source / manifest_name).read_text())
    metadata = {item['name']: item for item in source_manifest['assemblies' if assembly else 'results']}
    records = []
    for path in sorted(args.source.glob('*.SLDASM' if assembly else '*.SLDPRT')):
        if path.name.startswith('~$'):
            continue
        raw = path.read_bytes()
        archive = SldprtArchive.from_bytes(raw, path)
        streams = [(item.name, redact(item.data, args.redact_name)) for item in archive.records]
        prepared = BuildSldprt(streams, template=raw)
        target = args.destination / path.name
        target.write_bytes(prepared)
        original = metadata[path.name if assembly else path.stem]
        record = {
            'name': path.name,
            'source_sha256': hashlib.sha256(raw).hexdigest(),
            'sha256': hashlib.sha256(prepared).hexdigest(),
            'revision': source_manifest['build'] if assembly else original['revision'],
            'source_save': original['saved' if assembly else 'save'],
        }
        if assembly:
            record.update(
                source_components=original['components'],
                source_mates=original['mates'],
                source_whats_wrong=original['whats_wrong'],
                source_dialogs=original['dialogs'],
            )
        else:
            record.update(spec=original['spec'], source_bodies=original['bodies'], source_mass=original['mass'])
        records.append(record)
    if not records:
        raise ValueError(f'no {args.kind} controls found in {args.source}')
    manifest = {
        'provenance': 'Kit-authored SOLIDWORKS 2026 SP05.2 controls; metadata redacted at equal encoded width; container rebuilt from the same source',
        'acceptance': 'Research parser fixtures only; not generated writer output or held-out vendor acceptance',
        'kind': args.kind,
        'records': records,
    }
    (args.destination / 'Manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'prepared {len(records)} research controls')


if __name__ == '__main__':
    main()
