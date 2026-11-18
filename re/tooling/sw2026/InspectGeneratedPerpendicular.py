from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

from PerpendicularNativePlan import case_from_spec, check_predictions, check_state, native_trees, require


SCHEMA = 'kit.sw2026.generated-perpendicular-native-packet.v1'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
PHASES = ('control-before', 'generated', 'reopen', 'control-after')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def checked(path, expected):
    require(path.is_file() and not path.is_symlink() and digest(path) == expected, 'a frozen native probe input changed')
    return path


def verify(path, expected):
    root = path.parent.resolve(strict=True)
    job = load(checked(path, expected))
    require(job['schema'] == SCHEMA and job['oracle_sha256'] == ORACLE and job['heldout_inputs_read'] == 0
            and job['native_acceptance'] is False and job['public_writer_qualified'] is False,
            'use the bounded disclosed generated perpendicular packet')
    for name, wanted in job['tools_sha256'].items():
        checked(root / 'Tools' / name, wanted)
    for name, wanted in job['inputs_sha256'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'a packet input escapes its owner')
        checked(root / name, wanted)
    for name, item in job['generated_files'].items():
        for directory in ('FrozenGenerated', 'GeneratedInput'):
            checked(root / directory / name, item['sha256'])
    spec, prediction, request = (load(root / name) for name in ('Spec.json', 'Prediction.json', 'NeutralRequest.json'))
    require(load(root / 'Case.json') == case_from_spec(spec), 'the native case differs from the locked neutral intent')
    require(load(root / 'Trees.json') == native_trees(request), 'the native tree expectation differs from authored roles')
    check_predictions(load(root / 'Case.json'), prediction)
    return root, job


def input_hashes(root, job):
    values = {}
    for name, item in job['generated_files'].items():
        for directory in ('FrozenGenerated', 'GeneratedInput'):
            path = root / directory / name
            checked(path, item['sha256'])
            values[directory + '/' + name] = item['sha256']
    for role, row in job['control_files'].items():
        checked(Path(row['guest_path']), row['sha256'])
        values['control/' + role] = row['sha256']
    return values


def identity(row):
    require(row['version_matches'] and row['sha256'] == ORACLE and row['file_version'] == '34.5.2.0604'
            and type(row['process_creation_filetime']) is int and row['process_creation_filetime'] > 0,
            'the native oracle is not the pinned 2026 process')
    return {key: row[key] for key in ('process_id', 'process_creation_filetime', 'file_version', 'sha256')}


def previous(root, phase, expected):
    value = load(root / 'Inspection' / phase / 'Record.json')
    require(value['packet_sha256'] == expected and value['phase'] == phase and value['passed'] is True,
            'a required previous native phase did not pass')
    return value['result']


def check_control(author, value, expected, same_code):
    from PerpendicularMateEvidence import signature

    require(signature(value) == signature(expected), 'the pristine disclosed control changed native ownership or tree')
    for endpoint in value['mate']['ordered_endpoints']:
        require(all(endpoint['object_comparison'][key] == same_code for key in ('repeated_reference', 'repeated_specific')),
                'the pristine repeated-object control is unavailable')


def measure_control(author, controller, root, job, same_code):
    from PerpendicularMateEvidence import capture, same_file, signature

    case = load(root / 'ControlCase.json')
    expected = load(root / 'ControlState.json')
    parent, child = (Path(job['control_files'][key]['guest_path']) for key in ('parent', 'child'))
    model, errors, warnings = author.rec.call('open exact immutable perpendicular source control', controller.open, parent, read_only=True)
    require(model is not None and errors == warnings == 0 and same_file(author.get(model, 'GetPathName'), parent),
            'the disclosed control did not open cleanly at its exact identity')
    assembly = author.typed(model, 'AssemblyDoc')
    initial = capture(author, model, assembly, child, case)
    check_control(author, initial, expected, same_code)
    require(bool(author.get(model, 'ForceRebuild3', False)), 'the pristine perpendicular control did not rebuild')
    rebuilt = capture(author, model, assembly, child, case)
    check_control(author, rebuilt, expected, same_code)
    require(signature(initial) == signature(rebuilt), 'the pristine control changed across rebuild')
    return {'initial': initial, 'rebuilt': rebuilt, 'open_status': [errors, warnings], 'source_saved': False}


def generated_paths(root, job, saved=False):
    folder = root / ('Saved' if saved else 'GeneratedInput')
    return tuple(folder / job['generated_names'][key] for key in ('parent', 'child'))


def measure_generated(author, controller, root, job, phase, packet_sha, same_code):
    from AuthorPerpendicularMateSources import save_pair
    from PerpendicularMateEvidence import capture, component_map, edit_live, same_file, signature

    edited = phase == 'reopen'
    prior = previous(root, 'generated' if edited else 'control-before', packet_sha)
    case, prediction, trees, identities = (load(root / name) for name in ('Case.json', 'Prediction.json', 'Trees.json', 'GeneratedIdentity.json'))
    parent, child_path = generated_paths(root, job, edited)
    if edited:
        for role, path in zip(('parent', 'child'), (parent, child_path), strict=True):
            checked(path, prior['saved_files'][role]['sha256'])
    model, errors, warnings = author.rec.call('open exact generated perpendicular pair', controller.open, parent, read_only=edited)
    require(model is not None and errors == warnings == 0 and same_file(author.get(model, 'GetPathName'), parent),
            'the generated perpendicular pair did not open cleanly at its exact identity')
    assembly = author.typed(model, 'AssemblyDoc')
    value = {'open_status': [errors, warnings]}
    value['initial'] = capture(author, model, assembly, child_path, case, edited)
    initial = check_state(author, value['initial'], case, prediction, trees, identities, edited, same_code)
    author.rec.data['observations'] = value
    author.rec.flush()
    require(bool(author.get(model, 'ForceRebuild3', False)), 'the generated perpendicular assembly did not rebuild')
    value['rebuilt'] = capture(author, model, assembly, child_path, case, edited)
    require(initial == check_state(author, value['rebuilt'], case, prediction, trees, identities, edited, same_code),
            'the generated pair changed exact ownership across rebuild')
    if edited:
        require(initial == signature(prior['saved']), 'the saved generated pair changed ownership across fresh reopen')
        value['saved_files'] = prior['saved_files']
        return value
    child = author.get(component_map(author, assembly, case, child_path)[0], 'GetModelDoc2')
    edit_live(author, model, assembly, child, child_path, case)
    value['edited'] = capture(author, model, assembly, child_path, case, True)
    require(initial == check_state(author, value['edited'], case, prediction, trees, identities, True, same_code),
            'the valid pose and driving depth edit changed semantic ownership')
    saved_parent, saved_child = generated_paths(root, job, True)
    value['saved_files'] = save_pair(author, controller, model, assembly, child, saved_parent, saved_child)
    value['saved'] = capture(author, model, assembly, saved_child, case, True)
    require(initial == check_state(author, value['saved'], case, prediction, trees, identities, True, same_code),
            'the synchronized child-parent save changed exact ownership')
    value.update(valid_live_reorientation_and_depth_edit=True, active_angular_correction_proven=False)
    return value


def run_phase(root, job, phase, packet_sha):
    require(os.name == 'nt', 'native phases execute only inside the root-owned Windows guest')
    from AuthorCurves import CurveAuthor
    from AuthorPerpendicularMateSources import SourceRecorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from PerpendicularApiMetadata import metadata
    import Swapp

    require(root == Path(job['guest_root']).resolve(), 'the packet is not at its declared native linked identity')
    api = metadata()
    same_code = api['enums']['swObjectEquality']['swObjectSame']
    before = input_hashes(root, job)
    directory = root / 'Inspection' / phase
    directory.mkdir(parents=True, exist_ok=False)
    progress = directory / 'Progress.json'
    record = {'packet_sha256': packet_sha, 'phase': phase, 'stage': 'starting', 'passed': False, 'started_at': time.time()}
    def publish(**updates):
        record.update(updates)
        write(progress, record)
    recorder = SourceRecorder(directory / 'Record.json', {'packet_sha256': packet_sha, 'phase': phase}, publish)
    result, controller = {'passed': False, 'native_api_metadata': api}, None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call('verify exclusive idle generated perpendicular oracle', Swapp.sweep)
            controller = recorder.call('start owned generated perpendicular oracle', Swapp.Sw)
            actual = recorder.call('verify exact generated perpendicular oracle', application_identity, controller.app)
            result['oracle_identity'] = identity(actual)
            publish(stage='native_observation', identity=result['oracle_identity'])
            author = CurveAuthor(controller.app, recorder, Swapp)
            result.update(measure_control(author, controller, root, job, same_code) if phase.startswith('control-') else
                          measure_generated(author, controller, root, job, phase, packet_sha, same_code))
            result['passed'] = True
        except Exception as error:
            recorder.failure(error)
            result['error'] = repr(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result['controller_diagnostics'] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    result.update(dialogs=monitor.log, progress_windows=monitor.progress)
    try:
        result['input_hashes_before'] = before
        result['input_hashes_after'] = input_hashes(root, job)
        require(result['input_hashes_before'] == result['input_hashes_after'], 'the immutable native inputs changed')
        result['inputs_unchanged'] = True
    except Exception as error:
        recorder.failure(error)
        result['passed'] = False
    result['passed'] = bool(result['passed'] and not result['dialogs'] and not result.get('controller_diagnostics')
                            and recorder.data['first_failure'] is None and not recorder.data['cleanup_errors'])
    recorder.data.update(result=result, passed=result['passed'], phase=phase, packet_sha256=packet_sha, finished_at=time.time())
    recorder.flush()
    publish(stage='passed' if result['passed'] else 'failed', passed=result['passed'], record_sha256=digest(directory / 'Record.json'))
    require(result['passed'], 'the generated perpendicular native phase failed')


def summarize(root, packet_sha):
    rows = {phase: load(root / 'Inspection' / phase / 'Record.json') for phase in PHASES}
    require(all(row['packet_sha256'] == packet_sha and row['phase'] == key for key, row in rows.items()), 'mixed native packet receipts')
    identities = [row.get('result', {}).get('oracle_identity', {}) for row in rows.values()]
    times = [row.get('process_creation_filetime') for row in identities]
    passed = all(row['passed'] is True for row in rows.values()) and None not in times and len(set(times)) == 4
    result = {'schema': 'kit.sw2026.generated-perpendicular-native-result.v1', 'packet_sha256': packet_sha,
              'passed': passed, 'controls_healthy': all(rows[key]['passed'] for key in ('control-before', 'control-after')),
              'distinct_native_process_count': len(set(value for value in times if value is not None)),
              'numeric_checks': sum(len(row['checks']) for row in rows.values()),
              'phase_receipts': {key: digest(root / 'Inspection' / key / 'Record.json') for key in rows},
              'identities': identities, 'heldout_inputs_read': 0, 'public_writer_qualified': False,
              'valid_live_reorientation_and_depth_edit': bool(passed), 'active_angular_correction_proven': False}
    write(root / 'Inspection' / 'Result.json', result)
    print(json.dumps(result, sort_keys=True))
    require(passed, 'the controlled generated perpendicular lifecycle is incomplete')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('verify', 'run', 'summary'))
    parser.add_argument('job', type=Path)
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--phase', choices=PHASES)
    args = parser.parse_args()
    root, job = verify(args.job.resolve(strict=True), args.packet_sha256)
    if args.command == 'verify':
        print(json.dumps({'passed': True, 'packet_sha256': args.packet_sha256, 'native_processes_started': 0, 'heldout_inputs_read': 0}))
    elif args.command == 'summary':
        summarize(root, args.packet_sha256)
    else:
        require(args.phase is not None, 'the native probe requires an explicit isolated phase')
        directory = root / 'TransportLogs'
        directory.mkdir(exist_ok=True)
        with (directory / (args.phase + '.stdout.txt')).open('x', encoding='utf-8') as stdout:
            with (directory / (args.phase + '.stderr.txt')).open('x', encoding='utf-8') as stderr:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    run_phase(root, job, args.phase, args.packet_sha256)


if __name__ == '__main__':
    main()
