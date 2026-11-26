import argparse
import collections
import gzip
import hashlib
import json
import math
from pathlib import Path


def verify(root):
    manifest = json.loads((root / 'Manifest.json').read_text())
    cases = manifest['cases']
    if len(cases) != 96 or len({c['case']['id'] for c in cases}) != 96:
        raise ValueError('expected 96 distinct discovery cases')
    for artifact in manifest['artifacts']:
        path = root / artifact['path']
        if not path.is_relative_to(root) or '..' in Path(artifact['path']).parts:
            raise ValueError('artifact escapes package')
        payload = path.read_bytes()
        if len(payload) != artifact['size_bytes'] or hashlib.sha256(payload).hexdigest() != artifact['sha256']:
            raise ValueError('artifact identity mismatch: ' + artifact['path'])
        if path.suffix == '.gz':
            json.loads(gzip.decompress(payload))
    outcomes = collections.Counter()
    states = collections.Counter()
    for record in cases:
        states[record['status']] += 1
        for decode in record['decodes']:
            native = root / decode['native_path']
            if hashlib.sha256(native.read_bytes()).hexdigest() != decode['source_sha256']:
                raise ValueError('source identity mismatch')
            outcomes[decode['outcome']] += 1
            if decode['outcome'] == 'strict_decoded':
                document = json.loads(gzip.decompress((root / decode['neutral_report']).read_bytes()))
                if document['kind'] != 'kit.decode' or document['layer'] != 'neutral' or document['partial']:
                    raise ValueError('strict outcome differs from report')
            elif decode['outcome'] == 'strict_rejected':
                if decode['exit_code'] == 0 or decode['native_state_exit_code'] != 0 or not decode['strict_rejection']:
                    raise ValueError('rejected input lost its original strict outcome')
        if record['status'] != 'native_completed':
            if record['decodes'] or not record['error']:
                raise ValueError('blocked native outcome lacks diagnostic')
            continue
        truth = json.loads((root / 'Cases' / record['case']['id'] / 'GroundTruth.json').read_text())
        rows = truth['cases']
        if [r['case'] for r in rows] != ['control-before', 'variation', 'control-after']:
            raise ValueError('native control boundaries differ')
        for row in rows:
            volume = row.get('volume_cm3', row.get('volume_m3')) * (1000 if record['case']['application'] == 'fusion' else 1e9)
            params = row['parameters_mm']
            if not math.isclose(volume, math.prod(params.values()), rel_tol=1e-8):
                raise ValueError('native requested-volume check failed')
        if rows[0]['parameters_mm'] != rows[2]['parameters_mm']:
            raise ValueError('control restoration differs')
    if states != {'native_completed': 59, 'native_failed': 1, 'dispatch_blocked': 36}:
        raise ValueError('native outcome totals differ')
    if outcomes != {'strict_decoded': 57, 'strict_rejected': 120}:
        raise ValueError('reader outcome totals differ')
    return {'status': 'passed', 'artifacts': len(manifest['artifacts']), 'cases': len(cases), 'native_outcomes': dict(states), 'reader_outcomes': dict(outcomes), 'portable_complete': False, 'vendor_acceptance_established': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('select an unused report path')
    result = verify(Path(__file__).resolve().parent)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
