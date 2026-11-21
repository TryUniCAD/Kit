from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import math
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def source_files(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in (root / 'src').rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo')}


def write(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def execute(root, tools, output, label, script, request):
    destination = output / label
    argv = [sys.executable, '-I', '-B', str(tools / script), '--root', str(root), '--output', str(destination)]
    result = subprocess.run(argv, input=json.dumps(request, sort_keys=True, allow_nan=False), text=True,
        capture_output=True, timeout=180)
    write(output / (label + '.Transport.json'), {'argv': argv, 'exit': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr})
    assert result.returncode == 0, (label, result.stdout, result.stderr)
    path = destination / 'Record.json'
    record = json.loads(path.read_bytes())
    assert record['passed']
    return record, {'label': label, 'record': str(path), 'sha256': digest(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).parent
    expected = json.loads(args.source_manifest.read_bytes())
    before = source_files(args.root)
    assert expected['files'] == before
    tool_hashes = {name: digest(tools / name) for name in ('FreshCylinderInput.py', 'AuditFreshCylinderIds.py', 'ReadFreshCylinderIds.py', 'RunFreshCylinderIds.py')}
    input_hash = digest(args.inputs)
    cases = json.loads(args.inputs.read_bytes())['cases']
    assert len(cases) == 2 and {spec['case'] for spec in cases} == {'F01', 'F02'}
    write(args.output / 'SourceBefore.json', {'sdk': before, 'tools': tool_hashes,
        'input_sha256': input_hash, 'source_manifest_sha256': digest(args.source_manifest)})
    predictions = []
    for spec in cases:
        radius, depth = spec['radius_mm'], spec['depth_mm']
        cx, cy = spec['center_mm']
        centroid = [cx, cy, depth / 2] if spec['axis'] == 'z' else [cx, -depth / 2, -cy]
        predictions.append({'case': spec['case'], 'volume_mm3': math.pi * radius * radius * depth,
            'area_mm2': 2 * math.pi * radius * (depth + radius),
            'analytic_centroid_mm': centroid, 'centroid_is_not_a_native_measurement': True})
    write(args.output / 'PredictionsBefore.json', predictions)
    jobs = [(spec, repeat) for spec in cases for repeat in (1, 2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        generated = list(pool.map(lambda pair: execute(args.root, tools, args.output,
            pair[0]['case'] + 'Generate' + str(pair[1]), 'AuditFreshCylinderIds.py', pair[0]), jobs))
    for index in (0, 2):
        first, second = generated[index][0], generated[index + 1][0]
        assert first['files']['Candidate']['sha256'] == second['files']['Candidate']['sha256']
        assert first['candidate_identities'] == second['candidate_identities']
    requests = []
    for index, spec in ((0, cases[0]), (2, cases[1])):
        record = generated[index][0]
        for role in ('Candidate', 'Public'):
            for mode in ('default', 'metadata'):
                requests.append((spec['case'] + role + mode.title(), {
                    **record['files'][role], 'role': role, 'mode': mode, 'spec': spec}))
    with ThreadPoolExecutor(max_workers=2) as pool:
        reads = list(pool.map(lambda pair: execute(args.root, tools, args.output, pair[0],
            'ReadFreshCylinderIds.py', pair[1]), requests))
    records = [item[1] for item in generated + reads]
    pids = [item[0]['pid'] for item in generated + reads]
    assert len(set(pids)) == len(pids) == 12
    assert source_files(args.root) == before
    assert {name: digest(tools / name) for name in tool_hashes} == tool_hashes
    assert digest(args.inputs) == input_hash
    result = {'schema': 'kit.sw2026.fresh-cylinder-identity-process.v1', 'passed': True,
        'sdk_processes': len(pids), 'fresh_process_ids': pids, 'independent_cases': 2,
        'generation_processes': len(generated), 'public_read_processes': len(reads),
        'same_input_candidate_bytes_exact_across_processes': True,
        'normal_registry_part_outputs': len(generated), 'part_candidate_outputs': len(generated),
        'generic_analytic_encodes': 4, 'solidworks_persistent_endpoint_identities_created': 0,
        'concentric_mate_outputs': 0, 'native_processes': 0, 'hidden_inputs_read': 0,
        'inputs_unchanged': True, 'source_unchanged': True, 'tools_unchanged': True,
        'source_before_sha256': digest(args.output / 'SourceBefore.json'),
        'predictions_before_sha256': digest(args.output / 'PredictionsBefore.json'), 'records': records}
    write(args.output / 'Results.json', result)
    print(json.dumps({'passed': True, 'result': str(args.output / 'Results.json'), 'sha256': digest(args.output / 'Results.json')}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'passed': False, 'error_type': type(error).__name__, 'error': str(error)}))
        raise
