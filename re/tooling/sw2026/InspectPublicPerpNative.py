import argparse
from contextlib import redirect_stderr, redirect_stdout
from math import isclose
from pathlib import Path, PureWindowsPath
import json

import InspectGeneratedPerpendicular as native
from PerpendicularNativePlan import case_from_spec, check_predictions, native_trees, require
from PredictPublicPerp import intent, predict


SCHEMA = 'kit.sw2026.private-public-perpendicular-native-packet.v1'


def equal(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equal(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right, strict=True))
    if type(left) is float and type(right) in (float, int):
        return isclose(left, right, rel_tol=1e-12, abs_tol=1e-15)
    return left == right


def verify(path, expected):
    root = path.parent.resolve(strict=True)
    job = native.load(native.checked(path, expected))
    require(job['schema'] == SCHEMA and job['oracle_sha256'] == native.ORACLE
            and job['heldout_inputs_read'] == 0 and job['native_acceptance'] is False
            and job['public_writer_qualified'] is False and job['shared_registry_changed'] is False,
            'use the isolated ordinary public-registry perpendicular output packet')
    for name, wanted in job['tools_sha256'].items():
        native.checked(root / 'Tools' / name, wanted)
    for name, wanted in job['inputs_sha256'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'an input escapes this packet')
        native.checked(root / name, wanted)
    fixture = native.load(root / 'RegistryInput.json')
    require(fixture['native_parent'] == str(PureWindowsPath(job['guest_root']) / 'GeneratedInput' / job['generated_names']['parent']),
            'the registry input does not declare this exact native linked parent')
    for name, item in job['generated_files'].items():
        for directory in ('FrozenGenerated', 'GeneratedInput'):
            native.checked(root / directory / name, item['sha256'])
    proof = native.load(root / 'RegistryProof.json')
    require(proof['passed'] and proof['distinct_process_count'] == 27 and proof['runtime_input_file_reads'] == 0
            and proof['strict_default_rejects_unqualified_output'] and proof['public_native_qualification'] is False,
            'the real registry source-only proof is unavailable')
    spec, edit, expected_prediction = (native.load(root / name) for name in ('Spec.json', 'EditIntent.json', 'Prediction.json'))
    expected_intent = intent(fixture, edit)
    require(equal(native.load(root / 'PortableIntent.json'), expected_intent)
            and equal(expected_prediction, predict(fixture, edit)), 'the independent real neutral prediction changed')
    require(native.load(root / 'Case.json') == case_from_spec(spec), 'the lifecycle case differs from the disclosed neutral intent')
    require(native.load(root / 'Trees.json') == native_trees(native.load(root / 'TreeIntent.json')),
            'the default native roles differ from the frozen public recipe projection')
    check_predictions(native.load(root / 'Case.json'), expected_prediction)
    return root, job


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('verify', 'run', 'summary'))
    parser.add_argument('job', type=Path)
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--phase', choices=native.PHASES)
    args = parser.parse_args()
    root, job = verify(args.job.resolve(strict=True), args.packet_sha256)
    if args.command == 'verify':
        print(json.dumps({'passed': True, 'native_processes_started': 0, 'heldout_inputs_read': 0,
                          'packet_sha256': args.packet_sha256, 'shared_registry_changed': False}))
    elif args.command == 'summary':
        native.summarize(root, args.packet_sha256)
        result = native.load(root / 'Inspection/Result.json')
        result.update(schema='kit.sw2026.private-public-perpendicular-native-result.v1',
                      actual_registry_output_measured=True, public_writer_qualified=False,
                      shared_registry_changed=False, registry_source_flags_before_native=False)
        native.write(root / 'Inspection/Result.json', result)
        print(json.dumps(result, sort_keys=True))
    else:
        require(args.phase is not None, 'a single isolated native phase is required')
        directory = root / 'TransportLogs'
        directory.mkdir(exist_ok=True)
        with (directory / (args.phase + '.stdout.txt')).open('x', encoding='utf-8') as stdout:
            with (directory / (args.phase + '.stderr.txt')).open('x', encoding='utf-8') as stderr:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    native.run_phase(root, job, args.phase, args.packet_sha256)


if __name__ == '__main__':
    main()
