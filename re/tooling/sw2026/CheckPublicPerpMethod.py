import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def invoke(command, incoming, output, tag, success=True):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(incoming, timeout=180)
    (output / (tag + '.stdin.json')).write_bytes(incoming)
    (output / (tag + '.stdout.json')).write_bytes(stdout)
    (output / (tag + '.stderr.txt')).write_bytes(stderr)
    require((process.returncode == 0) == success, 'the disclosed method process has the wrong status ' + tag + ': ' + stderr.decode()[-1200:])
    return process.pid, json.loads(stdout) if stdout else None, sha256(stdout).hexdigest(), stderr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--method', type=Path, required=True)
    parser.add_argument('--method-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    path = args.method.resolve(strict=True)
    root = path.parent
    sys.path[:0] = [str(root / 'GuestTools'), str(root / 'NativeTools')]
    from VerifyPerpendicularFreeze import canonical, digest, verify
    from PerpendicularSourcePlan import disclosed_cases
    _, method = verify(path, args.method_sha256)
    require(method['compiler_entry'] == 'convert.write_document default registry', 'use the exact public method')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cases = disclosed_cases()
    translation = [sys.executable, '-I', '-B', str(root / 'EvaluationTools/TranslatePerpendicularCase.py'),
                   '--root', str(root / 'CodeRoot'), '--model-tools', str(root / 'WriterTools'),
                   '--native-root', r'C:\KitPublicPerpDisclosed\GeneratedInput']
    workers, results = [], []
    for case in (cases[0], cases[2]):
        tag = case['id']
        pid, value, stdout_sha, _ = invoke(translation, canonical(case), output, tag + 'Translate')
        workers.append(pid)
        require(value['source_files_read'] == value['native_processes_started'] == 0
                and not value['native_observations_used'] and value['existing_public_defaults_preserved'],
                'the public translator consumed unqualified source observations')
        fixture = value['request']['registry_input']
        builds = []
        for suffix in ('A', 'B'):
            request = dict(fixture, output=str(output / (tag + suffix)), allow_unqualified=True)
            pid, build, build_sha, _ = invoke([sys.executable, '-I', '-B', str(root / 'RegistryTools/GuardPublicPerpBuild.py'),
                                             str(root / 'CodeRoot')], canonical(request), output, tag + 'Build' + suffix)
            workers.append(pid)
            require(build['passed'] and build['round_trips'] == 22 and build['runtime_input_file_reads'] == 0,
                    'the disclosed normal registry crossed the source-only boundary')
            builds.append(build)
        require(builds[0]['artifacts'] == builds[1]['artifacts'], 'the public disclosed recipe did not reproduce complete bytes')
        child = case['child_name'] + '.SLDPRT'
        request = {'parent': str(output / (tag + 'A') / (case['name'] + '.SLDASM')),
                   'child': str(output / (tag + 'A') / child), 'prediction': value['prediction']}
        pid, read, read_sha, _ = invoke([sys.executable, '-I', '-B', str(root / 'WriterTools/VerifyPerpendicularGraph.py'),
                                       '--root', str(root / 'CodeRoot')], canonical(request), output, tag + 'Readback')
        workers.append(pid)
        require(read['passed'] and read['child_driver_count'] == 3, 'the actual public graph lost the native ownership or child drivers')
        results.append({'case': tag, 'translation_sha256': stdout_sha, 'readback_sha256': read_sha,
                        'complete_registry_files': {role: {key: item[key] for key in ('bytes', 'sha256')}
                                                   for role, item in builds[0]['artifacts'].items()},
                        'stream_round_trips': 44, 'independent_linked_geometry_and_drivers_equal': True})
    for tag, case, message in (('RejectReverse', cases[1], b'reverse native selection normalization'),
                               ('RejectSyntheticHostSlot', dict(deepcopy(cases[0]), id='H01', split='heldout'), b'sealed public translation is guest-only')):
        pid, value, _, stderr = invoke(translation, canonical(case), output, tag, False)
        workers.append(pid)
        require(value is None and message in stderr, 'the exact unsupported translation did not reject before output')
    verify(path, args.method_sha256)
    require(len(workers) == len(set(workers)) == 10, 'the disclosed process method lacks independent workers')
    receipt = {'schema': 'kit.sw2026.public-perpendicular-blind-method-disclosed-proof.v1', 'passed': True,
               'method_sha256': args.method_sha256, 'process_count': len(workers), 'cases': results,
               'reverse_selection_rejected': True, 'synthetic_host_slot_rejected': True,
               'synthetic_negative_contains_only_disclosed_D01_values': True,
               'runtime_input_file_reads_during_registry_generation': 0, 'native_processes_started': 0,
               'heldout_inputs_read': 0, 'new_public_writer_qualified': False}
    data = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    (output / 'DisclosedProof.json').write_bytes(data)
    print(json.dumps({'passed': True, 'process_count': 10, 'receipt_sha256': sha256(data).hexdigest(),
                      'heldout_inputs_read': 0, 'native_processes_started': 0}))


if __name__ == '__main__':
    main()
