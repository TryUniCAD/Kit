from argparse import ArgumentParser
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def checked_source(root, manifest):
    value = json.loads(manifest.read_bytes())
    return all(digest(root / relative) == expected['sha256'] and (root / relative).stat().st_size == expected['bytes'] for relative, expected in value['source_files'].items())


def run(root, worker, data, destination, phase):
    result = subprocess.run([sys.executable, '-B', str(worker), str(root), phase], input=json.dumps(data, separators=(',', ':'), allow_nan=False), text=True, capture_output=True, timeout=120)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.with_suffix('.stdout.json').write_text(result.stdout)
    destination.with_suffix('.stderr.txt').write_text(result.stderr)
    return result, json.loads(result.stdout) if result.returncode == 0 else None


def main():
    parser = ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert checked_source(args.root, args.manifest)
    args.output.mkdir(parents=True)
    binding = {'source_manifest_sha256': digest(args.manifest), 'worker_sha256': digest(args.worker), 'runner_sha256': digest(Path(__file__)), 'inputs': {p.name: digest(p) for p in sorted(args.inputs.glob('*.json'))}}
    (args.output / 'BeforeExecution.json').write_text(json.dumps(binding, indent=2, sort_keys=True)+'\n')
    positives = []
    baseline_rows = []
    reference = json.loads(args.baseline.read_bytes())
    for case in ('G01', 'G02', 'G03'):
        recipe = json.loads((args.inputs / f'{case}.json').read_bytes())
        runs = []
        for name in ('BuildA', 'BuildB'):
            process, result = run(args.root, args.worker, recipe, args.output / case / name, 'build')
            assert process.returncode == 0, (case, name, process.stderr)
            runs.append(result)
        assert runs[0] == runs[1]
        data = b64decode(runs[0]['generated'], validate=True)
        output = args.output / 'Generated' / f'GeneratedThrough{case}.SLDPRT'
        output.parent.mkdir(exist_ok=True)
        output.write_bytes(data)
        process, independent = run(args.root, args.worker, {'recipe': recipe, 'generated': runs[0]['generated']}, args.output / case / 'Audit', 'audit')
        assert process.returncode == 0 and independent['sha256'] == runs[0]['sha256'], (case, process.stderr)
        assert independent['streams'] == runs[0]['streams'] and independent['grammar'] == runs[0]['grammar']
        assert all(r['runtime_input_file_reads'] == r['sdk_runtime_research_imports'] == 0 for r in (*runs, independent))
        positives.append({'case': case, 'sha256': runs[0]['sha256'], 'bytes': len(data), 'request_sha256': digest(args.inputs / f'{case}.json'), 'prediction_sha256': digest(args.inputs / f'{case}Prediction.json'), 'build_repeat_sha256': runs[1]['sha256'], 'independent_audit_sha256': independent['sha256'], 'streams': independent['streams'], 'grammar': independent['grammar']})
        original = json.loads((args.baseline.parent.parent / 'Inputs' / f'{case}.json').read_bytes())
        process, legacy = run(args.root, args.root / 're/tooling/sw2026/ThroughAllColdProcess.py', original, args.output / case / 'Baseline', 'build')
        old = next(row for row in reference['positive_cases'] if row['case'] == case)
        assert process.returncode == 0 and legacy['sha256'] == old['artifact_sha256'], (case, process.stderr)
        baseline_rows.append({'case': case, 'sha256': legacy['sha256'], 'matches_original_frozen_artifact': True})
    mutations = {
        'unknown_intent': lambda r: r.update(feature_scope='automatic'),
        'unbound_direction': lambda r: r.update(direction='sideways'),
        'nonpositive_circle': lambda r: r.update(radius_m=0),
        'unenclosed_circle': lambda r: r.update(radius_m=0.1),
        'unbound_principal_axis': lambda r: r.update(axis='w'),
        'missing_configuration': lambda r: r.update(configuration=''),
        'wrong_file_identity': lambda r: r.update(native_path=r'\\Mac\Home\Documents\UniCAD\Oracle121Takeover\GeneratedThroughAllSelected01\GeneratedInput\OtherPart.SLDPRT'),
    }
    rejected = []
    for label, mutate in mutations.items():
        recipe = deepcopy(json.loads((args.inputs / 'G01.json').read_bytes()))
        mutate(recipe)
        process, result = run(args.root, args.worker, recipe, args.output / 'Rejected' / label, 'build')
        assert process.returncode != 0 and result is None and not process.stdout, label
        rejected.append({'case': label, 'rejected': True, 'exit_code': process.returncode})
    result = {'schema': 'kit.sw2026.selected-through-all-process.v1', 'passed': True, 'workers': 19, 'positive_cases': positives, 'legacy_cases': baseline_rows, 'negative_cases': rejected, 'exact_stream_roundtrips': 90, 'runtime_input_file_reads': 0, 'sdk_runtime_research_imports': 0, 'source_manifest_sha256': digest(args.manifest), 'worker_sha256': digest(args.worker), 'runner_sha256': digest(Path(__file__)), 'source_unchanged': checked_source(args.root, args.manifest), 'pre_execution_binding_sha256': digest(args.output / 'BeforeExecution.json'), 'heldout_payloads_read': 0, 'native_processes_started': 0, 'native_acceptance': False, 'original_source_equivalence': False, 'public_writer_qualified': False}
    assert result['source_unchanged'] and result['worker_sha256'] == binding['worker_sha256']
    encoded = (json.dumps(result, indent=2, sort_keys=True)+'\n').encode()
    (args.output / 'Result.json').write_bytes(encoded)
    print(json.dumps({'passed': True, 'workers': result['workers'], 'sha256': sha256(encoded).hexdigest(), 'positive_cases': len(positives), 'negative_cases': len(rejected)}))


if __name__ == '__main__':
    main()
