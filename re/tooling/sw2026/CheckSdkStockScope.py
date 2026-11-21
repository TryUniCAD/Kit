from argparse import ArgumentParser
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def check_source(root, manifest):
    values = json.loads(manifest.read_bytes())['source_files']
    assert all(digest(root / key) == value['sha256'] and (root / key).stat().st_size == value['bytes'] for key, value in values.items())


def main():
    parser = ArgumentParser()
    parser.add_argument('--preparation-root', type=Path, required=True)
    parser.add_argument('--reference-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prep = args.preparation_root.resolve(strict=True)
    root = prep / 'CodeRoot'
    worker = root / 're/tooling/sw2026/SdkSelectedScopeProcess.py'
    manifest = prep / 'MethodSourceManifest02.json'
    assert not args.output.exists()
    check_source(root, manifest)
    args.output.mkdir()
    binding = {'sdk_source_manifest_sha256': digest(manifest), 'worker_sha256': digest(worker), 'runner_sha256': digest(Path(__file__)), 'inputs': {p.name: digest(p) for p in sorted((prep / 'SelectedInputs').glob('*.json'))}, 'reference_result_sha256': digest(args.reference_root / 'Process02/Result.json')}
    assert binding['reference_result_sha256'] == '4156c18cb2c93ee9a8a2f4212cb8cc6ed5c32ae416186b6c2d14d02e2535cd53'
    (args.output / 'BeforeExecution.json').write_text(json.dumps(binding, indent=2, sort_keys=True)+'\n')
    records = []

    def run(label, request, phase, passed=True, baseline=False):
        program = root / 're/tooling/sw2026/ThroughAllColdProcess.py' if baseline else worker
        encoded = json.dumps(request, sort_keys=True, allow_nan=False).encode()
        value = subprocess.run([sys.executable, '-B', str(program), str(root), phase], input=encoded, capture_output=True, timeout=90)
        folder = args.output / label
        folder.mkdir(parents=True)
        (folder / 'Stdout.json').write_bytes(value.stdout)
        (folder / 'Stderr.txt').write_bytes(value.stderr)
        result = {'label': label, 'exit_code': value.returncode, 'input_sha256': sha256(encoded).hexdigest(), 'stdout_sha256': sha256(value.stdout).hexdigest(), 'stderr_sha256': sha256(value.stderr).hexdigest()}
        if passed:
            assert value.returncode == 0, (label, value.stderr.decode())
            parsed = json.loads(value.stdout)
            assert parsed['passed'] and parsed['runtime_input_file_reads'] == parsed['sdk_runtime_research_imports'] == 0
        else:
            assert value.returncode != 0 and not value.stdout and b'AssertionError' not in value.stderr and (b'ValueError:' in value.stderr or b'TypeError:' in value.stderr), (label, value.stderr.decode())
            parsed = None
        records.append(result)
        return parsed

    reference = json.loads((args.reference_root / 'Process02/Result.json').read_bytes())

    def positive(case):
        request = json.loads((prep / 'SelectedInputs' / f'{case}.json').read_bytes())
        left = run(case+'BuildA', request, 'build')
        right = run(case+'BuildB', request, 'build')
        assert left == right
        own = next(row for row in reference['positive_cases'] if row['case'] == case)
        assert left['sha256'] == own['sha256'] and left['streams'] == own['streams'] and left['grammar'] == own['grammar']
        independent = run(case+'Audit', {**request, 'generated': left['generated']}, 'audit')
        assert independent['sha256'] == left['sha256'] and independent['streams'] == left['streams'] and independent['grammar'] == left['grammar']
        artifact = args.output / 'Generated' / f'GeneratedThrough{case}.SLDPRT'
        artifact.parent.mkdir(exist_ok=True)
        artifact.write_bytes(b64decode(left['generated'], validate=True))
        plain = run(case+'ScopeZero', request['recipe'], 'build', baseline=True)
        changed = sorted(key for key in plain['streams'] if plain['streams'][key]['sha256'] != left['streams'][key]['sha256'])
        assert changed == ['Contents/Config-0', 'Contents/Config-0-ResolvedFeatures']
        return {'case': case, 'sha256': left['sha256'], 'bytes': left['bytes'], 'exact_prior_research_output': True, 'actual_stock_owner_retained': True, 'explicit_selection': left['explicit_selection'], 'grammar': left['grammar'], 'streams': left['streams'], 'only_changed_logical_streams': changed, 'scope_zero_sha256': plain['sha256']}

    with ThreadPoolExecutor(max_workers=3) as pool:
        positives = list(pool.map(positive, ('G01', 'G02', 'G03')))

    base_request = json.loads((prep / 'SelectedInputs/G01.json').read_bytes())
    faults = []
    variants = []
    for label, selection in (
        ('missing-selection', 'missing'),
        ('null-selection', None),
        ('empty-selection', {'mode': 'selected', 'body_ids': [], 'version': 19000}),
        ('duplicate-selection', {'mode': 'selected', 'body_ids': ['cut-body', 'cut-body'], 'version': 19000}),
        ('foreign-body-reference', {'mode': 'selected', 'body_ids': ['foreign-body'], 'version': 19000}),
        ('continuous-automatic', {'mode': 'automatic', 'body_ids': ['cut-body'], 'version': 19000}),
        ('all-bodies-fallback', {'mode': 'all_bodies', 'body_ids': ['cut-body'], 'version': 19000}),
        ('unsupported-release', {'mode': 'selected', 'body_ids': ['cut-body'], 'version': 18000}),
        ('boolean-release', {'mode': 'selected', 'body_ids': ['cut-body'], 'version': True}),
        ('extra-scope-intent', {'mode': 'selected', 'body_ids': ['cut-body'], 'version': 19000, 'auto_select': True}),
    ):
        request = deepcopy(base_request)
        if selection == 'missing':
            del request['selection']
        else:
            request['selection'] = selection
        variants.append((label, request))
    for label, probe in (
        ('foreign-stock-object', 'foreign_stock'),
        ('missing-typed-scope', 'none_scope'),
        ('unnamed-stock-owner', 'unnamed_stock'),
        ('prior-scope-state', 'existing_scope'),
        ('prior-stock-output', 'existing_output'),
        ('prior-manager-state', 'populated_manager'),
        ('retained-ghost-state', 'ghost_state'),
        ('foreign-feature-owner', 'foreign_feature'),
        ('unlisted-history-entry', 'unlisted_history'),
    ):
        request = deepcopy(base_request)
        request['probe'] = probe
        variants.append((label, request))
    for label, request in variants:
        run('Reject-'+label, request, 'build', False)
        faults.append(label)
    check_source(root, manifest)
    result = {'schema': 'kit.sw2026.selected-stock-sdk-process.v1', 'passed': True, 'workers': len(records), 'positive_cases': positives, 'negative_cases': faults, 'exact_selected_stream_roundtrips': 90, 'runtime_input_file_reads': 0, 'sdk_runtime_research_imports': 0, 'source_unchanged': True, 'source_manifest_sha256': digest(manifest), 'worker_sha256': digest(worker), 'runner_sha256': digest(Path(__file__)), 'before_execution_sha256': digest(args.output / 'BeforeExecution.json'), 'native_reference_result_sha256': 'f95b0c5e647d2312d483da7a0e95c4444d551705127ddea1978e9c6c405ceeeb', 'saved_reference_audit_sha256': '10141630ce384c68aa91f206edcd1814ab80f253ba7c3f279f317f53a16a4038', 'native_candidate_byte_equivalence': positives[0]['sha256'] == '339b4a635c9695306bcc8be512ba21f1473d97201a63b4ac668132ba7ef777a4', 'new_native_processes_started': 0, 'heldout_payloads_read': 0, 'original_source_equivalence': False, 'public_writer_qualified': False, 'processes': sorted(records, key=lambda value: value['label'])}
    path = args.output / 'Result.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'passed': True, 'workers': result['workers'], 'positive_cases': len(positives), 'negative_cases': len(faults), 'sha256': digest(path)}))


if __name__ == '__main__':
    main()
