import argparse
import base64
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_hash(path):
    return sha256(path.read_bytes()).hexdigest()


def verify_manifest(path, root):
    manifest = json.loads(path.read_bytes())
    for row in manifest['files']:
        source = root / row['path']
        require(source.is_file() and source.stat().st_size == row['bytes'] and file_hash(source) == row['sha256'],
            'frozen source differs: ' + row['path'])
    actual = {str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()}
    require(actual == {row['path'] for row in manifest['files']}, 'frozen source membership differs')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    require(not output.exists(), 'proof output already exists')
    verify_manifest(root / 'CodeSource01.json', root / 'Code01')
    verify_manifest(root / 'Baseline01Source.json', root / 'Baseline01')
    verify_manifest(root / 'ToolsSourceFinal02.json', root / 'Tools02')
    specs = json.loads((root / 'Specs01.json').read_bytes())['cases']
    sys.path.insert(0, str(root / 'Tools02'))
    from RevolveGeometry01 import predict_case
    output.mkdir(parents=True)
    report = {'schema': 'kit.sw2026.sdk-revolve-build-proof.v1', 'passed': False,
        'source_revision': '80094b57f8ea2e8d2312e613f8cd2875107a500e',
        'source_manifest_sha256': file_hash(root / 'CodeSource01.json'),
        'baseline_manifest_sha256': file_hash(root / 'Baseline01Source.json'),
        'tools_manifest_sha256': file_hash(root / 'ToolsSourceFinal02.json'),
        'specs_sha256': file_hash(root / 'Specs01.json'), 'runner_sha256': file_hash(Path(__file__)),
        'processes': [], 'positive_pairs': [], 'negative_variants': [], 'baseline_pairs': [],
        'heldout_inputs_read': 0, 'native_processes': 0}
    def checkpoint():
        (output / 'BuildProof.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    def worker(label, row, sdk='Code01', tool='AuditRevolveBuild01.py'):
        completed = subprocess.run([sys.executable, '-I', '-B', str(root / 'Tools02' / tool),
            '--sdk', str(root / sdk)], input=json.dumps(row), text=True, capture_output=True, timeout=90)
        (output / (label + '.stdout')).write_text(completed.stdout)
        (output / (label + '.stderr')).write_text(completed.stderr)
        evidence = {'name': label, 'exit_code': completed.returncode,
            'stdout_sha256': sha256(completed.stdout.encode()).hexdigest(),
            'stderr_sha256': sha256(completed.stderr.encode()).hexdigest()}
        report['processes'].append(evidence)
        checkpoint()
        require(completed.returncode == 0, 'process boundary failed: ' + label + '\n' + completed.stderr)
        value = json.loads(completed.stdout)
        require(value['passed'] and not value['runtime_external_attempts'], 'process assertions or runtime guard failed: ' + label)
        for module in value.get('sdk_modules', ()):
            require(Path(module).is_relative_to(root / sdk / 'src'), 'SDK import escaped the exact source closure')
        return value
    try:
        for index, spec in enumerate(specs):
            first = worker(f'Positive{index}A', {'spec': spec})
            second = worker(f'Positive{index}B', {'spec': spec})
            first_blob = base64.b64decode(first.pop('blob'), validate=True)
            second_blob = base64.b64decode(second.pop('blob'), validate=True)
            require(first_blob == second_blob and first == second, 'fresh process deterministic build differs')
            prediction = predict_case(spec)
            actual = first['geometry']; target = prediction['initial']
            for observed, expected in ((actual['volume_m3'], target['volume_m3']),
                (actual['area_m2'], target['area_m2']), *zip(actual['com_m'], target['center_of_mass_m'], strict=True)):
                require(isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-15), 'independent source predictor differs')
            (output / (spec['name'] + '.SLDPRT')).write_bytes(first_blob)
            (output / (spec['name'] + '.receipt.json')).write_text(json.dumps(first, indent=2, allow_nan=False)+'\n')
            (output / (spec['name'] + '.prediction.json')).write_text(json.dumps(prediction, indent=2, allow_nan=False)+'\n')
            report['positive_pairs'].append({'name': spec['name'], 'sha256': sha256(first_blob).hexdigest(),
                'bytes': len(first_blob), 'receipt_sha256': file_hash(output/(spec['name']+'.receipt.json')),
                'prediction_sha256': file_hash(output/(spec['name']+'.prediction.json')),
                'streams': first['streams'], 'graph': first['graph'], 'geometry': actual})
            checkpoint()
        mutations = ('expression','negative_angle','excess_angle','tiny_angle','nonfinite_angle',
            'two_sided','axis_in_contour','missing_axis_relation','fixed_axis','extra_metadata',
            'body_name','support_origin','alternate_unit','wrong_relation','axis_relation','downward_axis',
            'axis_origin','additional_configuration')
        for index, mutation in enumerate(mutations):
            value = worker(f'Negative{index}', {'spec': specs[1], 'mutation': mutation})
            require(value['rejected'], 'unsupported neutral source was not rejected')
            report['negative_variants'].append({'mutation': mutation, 'error_class': value['error_class'],
                'error_message': value['error_message']})
            checkpoint()
        for index, spec in enumerate((specs[0], specs[3])):
            row = {'spec': spec, 'depth_mm': 11.375 + index * 9.25}
            before = worker(f'BaselinePolygon{index}', row, 'Baseline01', 'AuditPolygonControl01.py')
            after = worker(f'CandidatePolygon{index}', row, 'Code01', 'AuditPolygonControl01.py')
            require(before == after and before['lines'] == 4, 'existing ordinary polygon writer bytes or readback changed')
            report['baseline_pairs'].append(before)
        report['passed'] = True
    except Exception as error:
        report['error'] = repr(error)
    finally:
        report['fresh_processes'] = len(report['processes'])
        checkpoint()
    print(json.dumps({'passed': report['passed'], 'fresh_processes': report['fresh_processes'],
        'positives': len(report['positive_pairs']), 'negatives': len(report['negative_variants']),
        'baseline_pairs': len(report['baseline_pairs']), 'proof_sha256': file_hash(output/'BuildProof.json')}))
    return 0 if report['passed'] else 3


if __name__ == '__main__':
    raise SystemExit(main())
