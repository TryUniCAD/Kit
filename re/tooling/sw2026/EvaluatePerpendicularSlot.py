import argparse
from base64 import b64decode
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PreparePerpendicularSlot import fixed_root
from VerifyPerpendicularFreeze import canonical, digest, load, require, runtime, verify


PHASES = ('control-before', 'source', 'source-edited', 'generated', 'reopen', 'control-after')


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    return digest(path)


def preparation(root, method, args):
    folder = fixed_root(args.private_root) / args.method_sha256 / args.slot / 'Prepared'
    fixed_root(folder)
    record = load(folder / 'PreparationLock.json')
    require(record['method_sha256'] == args.method_sha256 and record['slot'] == args.slot
            and record['native_source_files_opened'] == record['native_source_observations_opened'] == 0,
            'the neutral preparation was not locked before observation')
    require(record['runtime_sha256'] == sha256(canonical(runtime())).hexdigest(), 'the frozen guest runtime changed')
    for name, field in (('NeutralCase.json', 'selected_neutral_sha256'), ('NeutralRequest.json', 'request_sha256'),
                        ('Prediction.json', 'prediction_sha256'), ('Trees.json', 'trees_sha256')):
        require(digest(folder / name) == record[field], 'a locked neutral input or expectation changed')
    case = load(folder / 'NeutralCase.json')
    require(case['id'] == method['slots'][args.slot]['case_id'], 'the private neutral case does not belong to its released slot')
    return folder, record, case


def process(command, incoming, folder, tag):
    result = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = result.communicate(incoming, timeout=180)
    (folder / (tag + '.stdout.json')).write_bytes(stdout)
    (folder / (tag + '.stderr.txt')).write_bytes(stderr)
    require(result.returncode == 0, 'a frozen source-only SDK worker failed')
    return json.loads(stdout), result.pid


def build(root, folder, preparation_record, case):
    require(not (folder / 'BuildLock.json').exists(), 'the sealed generated build must not overwrite a prior result')
    request = (folder / 'NeutralRequest.json').read_bytes()
    code = root / 'CodeRoot'
    command = [sys.executable, '-I', '-B', str(code / 're/tooling/sw2026/SdkPlanarGroupProcess.py'), str(code)]
    first, left = process(command, request, folder, 'BuildA')
    second, right = process(command, request, folder, 'BuildB')
    values = [dict(first), dict(second)]
    for value in values:
        require(value['passed'] and value['runtime_input_file_reads'] == value['sdk_runtime_research_imports'] == 0,
                'the sealed build crossed the source-only boundary')
        value.pop('worker_pid')
    require(values[0] == values[1] and left != right, 'the sealed build is not deterministic in separate processes')
    generated = folder / 'GeneratedInput'
    generated.mkdir(exist_ok=False)
    names = {'parent': case['name'] + '.SLDASM', 'child': case['child_name'] + '.SLDPRT'}
    for role, source in (('parent', 'assembly'), ('child', 'child')):
        (generated / names[role]).write_bytes(b64decode(first[source]['blob'], validate=True))
    read_request = {'parent': str(generated / names['parent']), 'child': str(generated / names['child']),
                    'prediction': load(folder / 'Prediction.json')}
    readback, worker = process([sys.executable, '-I', '-B', str(root / 'WriterTools/VerifyPerpendicularGraph.py'), '--root', str(code)],
                               canonical(read_request), folder, 'TypedReadback')
    require(readback['passed'] and len({left, right, worker}) == 3, 'the sealed complete typed graph does not match independent expectations')
    identities = {'mate_id': first['endpoints'][0]['mate_id'], 'endpoints': readback['actual_owned_endpoints']}
    write(folder / 'GeneratedIdentity.json', identities)
    write(folder / 'Case.json', case)
    for name in ('ControlCase.json', 'ControlState.json'):
        (folder / name).write_bytes((root / 'Inputs' / name).read_bytes())
    files = {role: {'sha256': digest(generated / name), 'bytes': (generated / name).stat().st_size} for role, name in names.items()}
    lock = {'schema': 'kit.sw2026.perpendicular-sealed-generated-build-lock.v1',
            'preparation_lock_sha256': digest(folder / 'PreparationLock.json'), 'request_sha256': preparation_record['request_sha256'],
            'prediction_sha256': preparation_record['prediction_sha256'], 'generated_names': names, 'generated_files': files,
            'generated_identity_sha256': digest(folder / 'GeneratedIdentity.json'), 'case_sha256': digest(folder / 'Case.json'),
            'runtime_input_file_reads': 0, 'sdk_runtime_research_imports': 0, 'native_processes_started': 0,
            'native_source_files_opened': 0, 'native_source_observations_opened': 0, 'worker_count': 3}
    lock_sha = write(folder / 'BuildLock.json', lock)
    return {'passed': True, 'build_lock_sha256': lock_sha, 'generated_files': files, 'worker_count': 3,
            'runtime_input_file_reads': 0, 'sdk_runtime_research_imports': 0, 'native_processes_started': 0}


def locked_build(folder):
    lock = load(folder / 'BuildLock.json')
    require(lock['preparation_lock_sha256'] == digest(folder / 'PreparationLock.json') and
            lock['generated_identity_sha256'] == digest(folder / 'GeneratedIdentity.json') and
            lock['case_sha256'] == digest(folder / 'Case.json'), 'a generated proof input changed before native observation')
    for role, name in lock['generated_names'].items():
        require(digest(folder / 'GeneratedInput' / name) == lock['generated_files'][role]['sha256'], 'a generated original changed')
    return lock


def source_inputs(method, slot, case):
    source_packet = Path(method['source_packet_guest_path'])
    lock_file = source_packet / 'Progress' / slot['case_id'] / 'lock/Record.json'
    require(digest(lock_file) == slot['source_lock_sha256'], 'the original source lock changed')
    lock = load(lock_file)
    metadata = load(source_packet / 'Source.json')
    private = fixed_root(Path(metadata['guest_private_base'])) / method['source_packet_sha256'] / slot['case_id']
    fixed_root(private)
    files = {}
    for state, directory in (('source', 'Source'), ('edited', 'Edited')):
        files[state] = {}
        for role, name in (('parent', case['name'] + '.SLDASM'), ('child', case['child_name'] + '.SLDPRT')):
            path = private / 'Native' / directory / name
            require(digest(path) == lock['native_artifacts'][state][role]['sha256'], 'an immutable native source changed')
            files[state][role] = path
    observations = private / 'SavedAuthor.json'
    require(digest(observations) == lock['source_manifest_sha256'], 'the locked native source observation changed')
    return files, observations


def source_phase(author, controller, case, files, observations, edited):
    from PerpendicularMateEvidence import capture, same_file, signature

    key = 'edited' if edited else 'source'
    parent, child = (files[key][role] for role in ('parent', 'child'))
    original = load(observations)[key]
    model, errors, warnings = author.rec.call('open exact locked native source read only', controller.open, parent, read_only=True)
    require(model is not None and errors == warnings == 0 and same_file(author.get(model, 'GetPathName'), parent), 'the exact native source failed to open cleanly')
    assembly = author.typed(model, 'AssemblyDoc')
    initial = capture(author, model, assembly, child, case, edited)
    require(signature(initial) == signature(original), 'the source native tree or ownership changed from its independent lock')
    require(bool(author.get(model, 'ForceRebuild3', False)), 'the native source did not rebuild')
    rebuilt = capture(author, model, assembly, child, case, edited)
    require(signature(rebuilt) == signature(initial), 'the native source changed ownership on rebuild')
    return {'initial': initial, 'rebuilt': rebuilt, 'open_status': [errors, warnings], 'source_saved': False}


def native_phase(root, method, args, folder, case, phase):
    sys.path[:0] = [str(root / 'NativeTools'), str(root / 'EvaluationTools')]
    from AuthorCurves import CurveAuthor
    from AuthorPerpendicularMateSources import SourceRecorder
    from InspectGeneratedPerpendicular import identity, measure_control, measure_generated, previous
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from PerpendicularApiMetadata import metadata
    import Swapp

    files, observations, original_hashes = None, None, {}
    job = {'control_files': method['control_files']}
    if not phase.startswith('control-'):
        build_lock = locked_build(folder)
        previous(folder, 'control-before', args.method_sha256)
        if phase == 'source-edited':
            previous(folder, 'source', args.method_sha256)
        if phase == 'generated':
            previous(folder, 'source', args.method_sha256)
            previous(folder, 'source-edited', args.method_sha256)
        files, observations = source_inputs(method, method['slots'][args.slot], case)
        original_hashes = {str(path): digest(path) for row in files.values() for path in row.values()}
        original_hashes[str(observations)] = digest(observations)
        for role, name in build_lock['generated_names'].items():
            original_hashes[str(folder / 'GeneratedInput' / name)] = build_lock['generated_files'][role]['sha256']
        job['generated_names'] = build_lock['generated_names']
    for row in method['control_files'].values():
        require(digest(Path(row['guest_path'])) == row['sha256'], 'the disclosed bracketing control changed')
        original_hashes[row['guest_path']] = row['sha256']
    directory = folder / 'Inspection' / phase
    directory.mkdir(parents=True, exist_ok=False)
    progress = {'passed': False, 'slot': args.slot, 'phase': phase, 'stage': 'native_starting', 'method_sha256': args.method_sha256}
    def publish(**updates):
        progress.update(updates)
        temporary = args.public_output.with_suffix('.tmp')
        temporary.write_text(json.dumps(progress, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        temporary.replace(args.public_output)
    recorder = SourceRecorder(directory / 'Record.json', {'slot': args.slot, 'phase': phase, 'method_sha256': args.method_sha256}, publish)
    result, controller = {'passed': False}, None
    api = metadata()
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call('verify exclusive idle sealed oracle', Swapp.sweep)
            controller = recorder.call('start fresh owned sealed oracle', Swapp.Sw)
            result['oracle_identity'] = identity(recorder.call('verify pinned sealed oracle', application_identity, controller.app))
            publish(stage='native_observation', identity=result['oracle_identity'])
            author = CurveAuthor(controller.app, recorder, Swapp)
            if phase.startswith('control-'):
                result.update(measure_control(author, controller, folder, job, api['enums']['swObjectEquality']['swObjectSame']))
            elif phase.startswith('source'):
                result.update(source_phase(author, controller, case, files, observations, phase == 'source-edited'))
            else:
                result.update(measure_generated(author, controller, folder, job, phase, args.method_sha256,
                                                api['enums']['swObjectEquality']['swObjectSame']))
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
    result['inputs_unchanged'] = all(digest(Path(path)) == wanted for path, wanted in original_hashes.items())
    result['passed'] = bool(result['passed'] and result['inputs_unchanged'] and not result['dialogs']
                            and not result.get('controller_diagnostics') and not recorder.data['cleanup_errors']
                            and recorder.data['first_failure'] is None)
    recorder.data.update(result=result, passed=result['passed'], packet_sha256=args.method_sha256, phase=phase, finished_at=time.time())
    recorder.flush()
    require(result['passed'], 'the sealed native phase failed')
    return {'passed': True, 'phase': phase, 'identity': result['oracle_identity'], 'record_sha256': digest(directory / 'Record.json'),
            'numeric_checks': len(recorder.data['checks']), 'inputs_unchanged': True, 'native_processes_started': 1}


def finalize(root, method, args, folder, case):
    sys.path.insert(0, str(root / 'EvaluationTools'))
    from ComparePerpendicularNative import compare

    records = {phase: load(folder / 'Inspection' / phase / 'Record.json') for phase in PHASES}
    require(all(row['passed'] and row['packet_sha256'] == args.method_sha256 and row['phase'] == phase
                and row['result']['inputs_unchanged'] for phase, row in records.items()), 'not all sealed native phases qualified')
    identities = [row['result']['oracle_identity'] for row in records.values()]
    require(len({(row['process_id'], row['process_creation_filetime']) for row in identities}) == 6, 'the sealed native phases are not independent')
    prediction = load(folder / 'Prediction.json')
    comparisons = []
    for source, generated, key, edited in (('source', 'generated', 'initial', False), ('source', 'generated', 'rebuilt', False),
                                          ('source-edited', 'generated', 'edited', True), ('source-edited', 'generated', 'saved', True),
                                          ('source-edited', 'reopen', 'initial', True), ('source-edited', 'reopen', 'rebuilt', True)):
        comparisons.append(compare(case, records[source]['result']['rebuilt'], records[generated]['result'][key], prediction, edited))
    files, observations = source_inputs(method, method['slots'][args.slot], case)
    audits = []
    sys.path.insert(0, str(root / 'CodeRoot/src'))
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    pairs = [(state, files[state], records['source-edited' if state == 'edited' else 'source']['result']['rebuilt']) for state in ('source', 'edited')]
    build_lock = locked_build(folder)
    pairs.append(('generated-saved', {role: folder / 'Saved' / name for role, name in build_lock['generated_names'].items()},
                  records['reopen']['result']['rebuilt']))
    for label, pair, expected in pairs:
        parent, child = pair['parent'], pair['child']
        stream = SldprtArchive.from_bytes(parent.read_bytes()).require('Contents/Config-0-MatesList')
        request = {'path': str(parent), 'sha256': digest(parent), 'bytes': parent.stat().st_size,
                   'stream_sha256': sha256(stream).hexdigest(), 'child_path': str(child),
                   'child_sha256': digest(child), 'expected': expected}
        audit, process_id = process([sys.executable, '-I', '-B', str(root / 'ReaderTools/AuditPerpendicularReader.py'),
                                     '--root', str(root / 'CodeRoot')], canonical(request), folder, 'Readback-' + label)
        require(audit['passed'] and audit['public']['status'] == 'admitted' and audit['public']['child_driver_count'] == 3,
                'the sealed source or generated saved pair failed normal SDK readback')
        audits.append({'state': label, 'parent_sha256': digest(parent), 'child_sha256': digest(child),
                       'public_status': audit['public']['status'], 'child_drivers': audit['public']['child_driver_count'],
                       'audit_sha256': digest(folder / ('Readback-' + label + '.stdout.json'))})
    receipt = {'schema': 'kit.sw2026.perpendicular-sealed-native-evaluation.v1', 'passed': True, 'slot': args.slot,
               'method_sha256': args.method_sha256, 'preparation_lock_sha256': digest(folder / 'PreparationLock.json'),
               'build_lock_sha256': digest(folder / 'BuildLock.json'), 'native_process_count': 6,
               'numeric_checks': sum(len(row['checks']) for row in records.values()), 'identities': identities,
               'phase_hashes': {phase: digest(folder / 'Inspection' / phase / 'Record.json') for phase in PHASES},
               'paired_comparison_count': len(comparisons), 'all_paired_comparisons_passed': all(row['passed'] for row in comparisons),
               'ordered_native_trees_and_semantic_owners_equal': True, 'measured_paired_mass_equal': True,
               'independent_geometry_and_poses_equal': True, 'child_drivers': 3, 'strict_public_saved_and_source_readbacks': audits,
               'controls_healthy': True, 'immutable_inputs_unchanged': True, 'runtime_input_file_reads_during_generation': 0,
               'sdk_runtime_research_imports': 0, 'active_invalid_angle_correction_proven': False,
               'public_perpendicular_writer_qualified': False}
    write(folder / 'FinalResult.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('build', 'native', 'finalize'))
    parser.add_argument('method', type=Path)
    parser.add_argument('--method-sha256', required=True)
    parser.add_argument('--slot', choices=('Slot01', 'Slot02'), required=True)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--public-output', type=Path, required=True)
    parser.add_argument('--phase', choices=PHASES)
    args = parser.parse_args()
    require(os.name == 'nt', 'sealed evaluation executes only in the root-owned guest')
    root, method = verify(args.method.resolve(strict=True), args.method_sha256)
    folder, locked, case = preparation(root, method, args)
    require(not args.public_output.exists(), 'sealed public progress must preserve all previous receipts')
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    write(args.public_output, {'passed': False, 'slot': args.slot, 'stage': args.command,
                               'method_sha256': args.method_sha256, 'phase': args.phase})
    tag = args.command + ('-' + args.phase if args.phase else '')
    try:
        with (folder / (tag + '.stdout.txt')).open('x', encoding='utf-8') as stdout:
            with (folder / (tag + '.stderr.txt')).open('x', encoding='utf-8') as stderr:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    if args.command == 'build':
                        result = build(root, folder, locked, case)
                    elif args.command == 'native':
                        require(args.phase is not None, 'a native phase must be explicit and isolated')
                        result = native_phase(root, method, args, folder, case, args.phase)
                    else:
                        result = finalize(root, method, args, folder, case)
                    verify(root / 'Method.json', args.method_sha256)
    except Exception:
        failure = folder / (tag + '.Failure.txt')
        failure.write_text(traceback.format_exc(), encoding='utf-8')
        result = {'passed': False, 'slot': args.slot, 'stage': args.command, 'phase': args.phase,
                  'method_sha256': args.method_sha256, 'private_failure_sha256': digest(failure), 'native_acceptance': False}
        write(args.public_output, result)
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(3)
    result.update(slot=args.slot, method_sha256=args.method_sha256, phase=args.phase)
    write(args.public_output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
