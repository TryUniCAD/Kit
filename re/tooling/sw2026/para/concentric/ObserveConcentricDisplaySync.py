from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
import sys
import time


sys.path.insert(0, str(Path(__file__).resolve().parent))

import ObserveConcentricDisplayOracle as display
from ConcentricNativeContract import ORACLE, checked, digest, require, signature, write_json
from InspectGeneratedConcentric import capture, components, same_file


GATE_SCHEMA = 'kit.sw2026.concentric-display-child-cut.v1'
LANES = ('Stale', 'Synchronized')
ROLES = ('ControlBefore', 'Author', *LANES, 'ControlAfter')


def context(packet, sha):
    root, job, source, pair, prediction, states = display.verify(packet, sha)
    require(job['sync_from_trial_sha256'] == 'eace2beb513a3f02ba7a053a6622a1d793f12f55f288e9cc9a675c9b41daa048'
            and Path(__file__).resolve() == root / 'Tools' / Path(__file__).name, 'the frozen same-parent probe is required')
    for relative in ('Revisions', 'Revisions/Stale', 'Revisions/Synchronized'):
        folder = root / relative
        require(folder.is_dir() and folder.resolve() == folder and not folder.is_symlink() and not folder.is_junction(),
                'the private revision directory was redirected')
    return root, job, source, pair, prediction, states


def snapshots(root, pair):
    return {'parent': root / 'Revisions' / pair[0].name,
            **{lane: root / 'Revisions' / lane / pair[1].name for lane in LANES}}


def retain(source, target, sha):
    with target.open('xb') as stream:
        stream.write(checked(source, sha).read_bytes())
    checked(target, sha)


def wire_gate(root, trial_sha, gate_sha, pair):
    require(gate_sha is not None, 'the host typed stamp gate is required before a cold dispatch')
    value = json.loads(checked(root / 'Gate.json', gate_sha).read_bytes())
    require(value['schema'] == GATE_SCHEMA and value['trial_sha256'] == trial_sha and value['passed'] is True
            and value['author_record_sha256'] == digest(root / 'Inspection/Author/Record.json'), 'the host gate is not bound to these saves')
    known = display.previous(root, trial_sha, 'Author')
    require(value['artifact_sha256'] == known['revision_sha256'] and value['live_child_stamp'] == known['live_child_stamp']
            and value['parent_reference_stamps'] == [value['live_child_stamp']] * 2
            and value['child_persisted_stamps']['Synchronized'] == value['live_child_stamp']
            and value['child_persisted_stamps']['Stale'] != value['live_child_stamp'], 'the host gate changed the intervention')
    for key, path in snapshots(root, pair).items():
        checked(path, value['artifact_sha256'][key])
    checked(pair[0], value['artifact_sha256']['parent'])
    return value, known


def stage(packet, trial_sha, lane, gate_sha):
    root, _, _, pair, _, _ = context(packet, trial_sha)
    gate, _ = wire_gate(root, trial_sha, gate_sha, pair)
    if lane == 'Synchronized':
        require(display.phase_record(root, trial_sha, 'Stale') is not None, 'the stale cold open must have been attempted first')
    receipt = root / 'Inspection' / f'Stage{lane}.json'
    require(not receipt.exists(), 'a stage can use its owned revision once')
    other = 'Synchronized' if lane == 'Stale' else 'Stale'
    checked(pair[1], gate['artifact_sha256'][other])
    import Swapp

    Swapp.sweep()
    checked(pair[0], gate['artifact_sha256']['parent'])
    checked(pair[1], gate['artifact_sha256'][other])
    pending = pair[1].with_suffix('.pending')
    retain(snapshots(root, pair)[lane], pending, gate['artifact_sha256'][lane])
    pending.replace(pair[1])
    files = display.file_hashes(pair)
    require(files == {'parent': gate['artifact_sha256']['parent'], 'child': gate['artifact_sha256'][lane]},
            'the final locators do not contain the selected exact pair')
    write_json(receipt, {'trial_sha256': trial_sha, 'gate_sha256': gate_sha, 'lane': lane, 'working_hashes': files,
                         'native_launches': 0, 'passed': True})
    return True


def document_state(author, model):
    extension = author.get(model, 'Extension')
    return {'path': str(author.get(model, 'GetPathName')), 'document_type': int(author.get(model, 'GetType')),
            'update_stamp': int(author.get(model, 'GetUpdateStamp')), 'needs_rebuild': int(author.get(extension, 'NeedsRebuild2')),
            'whats_wrong': int(author.get(extension, 'GetWhatsWrongCount')), 'save_flag': bool(author.get(model, 'GetSaveFlag')),
            'configuration': str(author.get(author.get(model, 'GetActiveConfiguration'), 'Name'))}


def named_and_active(author, config, assembly, child_path, occurrences, states, result):
    default = states[0]
    names = tuple(name for name, _ in states)
    result['opening_display_states'] = display.inventory(author, config, names, default[0])
    _, result['opening_occurrences'] = display.live_visibility(author, assembly, child_path, occurrences, default)
    named, active = {}, {}
    result['visibility'] = {'named': named, 'active': active}
    for state in states:
        named[state[0]] = display.named_visibility(author, config, state, child_path, occurrences)
    for state in (*reversed(states[1:]), default):
        display.apply(author, config, state[0])
        display.inventory(author, config, names, state[0])
        _, active[state[0]] = display.live_visibility(author, assembly, child_path, occurrences, state)
        require(all(row['visible'] == named[state[0]][name]['visible'] for name, row in active[state[0]].items()),
                'the named and active visibility readings disagree')


def resolved_child(author, assembly, child_path, prediction):
    child = author.get(components(author, assembly, child_path, prediction)[0], 'GetModelDoc2')
    require(child is not None and same_file(author.get(child, 'GetPathName'), child_path), 'the owned child was not resolved')
    return child


def finish_author(author, model, config, assembly, pair, prediction, states, result, target, revision_paths):
    require(author.get(model, 'ForceRebuild3', False) is True, 'the owned source did not rebuild')
    result['initial'], _ = capture(author, model, assembly, pair[1], prediction)
    occurrences = {item['name']: item for item in result['initial']['occurrences']}
    display.author_states(author, model, config, assembly, pair, prediction, occurrences, states, result, target)
    saved = result['saved']['files_sha256']
    retain(pair[0], revision_paths['parent'], saved['parent'])
    retain(pair[1], revision_paths['Stale'], saved['child'])
    child = resolved_child(author, assembly, pair[1], prediction)
    live = document_state(author, child)
    result['child_before_own_save'] = live
    require(live['document_type'] == 1 and live['configuration'] == prediction['child_configuration']
            and same_file(live['path'], pair[1]) and not author.get(child, 'IsOpenedReadOnly')
            and not pair[1].samefile(revision_paths['Stale']), 'the loaded child save is outside its owned file')
    sw = author.sw
    author.get(child, 'SetSaveFlag')
    require(author.get(child, 'GetSaveFlag') is True, 'the owned child did not become dirty')
    errors, warnings = sw.byref_long(), sw.byref_long()
    ok = author.rec.call('save only the already loaded owned child after the final parent save', sw.invoke, child,
                         'Save3', sw.SAVE_SILENT, errors, warnings)
    result['child_save_status'] = [bool(ok), int(errors.value), int(warnings.value)]
    result['child_after_own_save'] = document_state(author, child)
    actual = display.file_hashes(pair)
    require(result['child_save_status'] == [True, 0, 0] and actual['parent'] == saved['parent']
            and actual['child'] != saved['child'] and result['child_after_own_save']['update_stamp'] == live['update_stamp']
            and same_file(result['child_after_own_save']['path'], pair[1]), 'saving the child changed the parent or live stamp')
    retain(pair[1], revision_paths['Synchronized'], actual['child'])
    result['revision_sha256'] = {'parent': actual['parent'], 'Stale': saved['child'], 'Synchronized': actual['child']}
    result['live_child_stamp'] = live['update_stamp']
    result['after_child_save'], _ = capture(author, model, assembly, pair[1], prediction)
    require(signature(result['after_child_save']) == signature(result['rebuilt']), 'the child-only save changed observed geometry or native ownership')


def finish_diagnostic(author, model, config, assembly, pair, prediction, states, result, prior, gate, role):
    observed = {'parent': document_state(author, model)}
    result['before_rebuild'] = observed
    child = resolved_child(author, assembly, pair[1], prediction)
    observed['child'] = document_state(author, child)
    result['persisted_child_stamp'] = gate['child_persisted_stamps'][role]
    require(same_file(observed['parent']['path'], pair[0]) and same_file(observed['child']['path'], pair[1])
            and observed['parent']['document_type'] == 2 and observed['child']['document_type'] == 1
            and observed['parent']['configuration'] == prediction['parent_configuration']
            and observed['child']['configuration'] == prediction['child_configuration'], 'cold documents lost their owned paths, types or configurations')
    occurrences = {row['name']: row for row in prior['after_child_save']['occurrences']}
    named_and_active(author, config, assembly, pair[1], occurrences, states, result)
    require(result['visibility']['named'] == prior['observed']['named'], 'the cold named readback differs from the author')
    require(author.get(model, 'ForceRebuild3', False) is True, 'the restored default failed its native rebuild')
    result['rebuilt'], _ = capture(author, model, assembly, pair[1], prediction)
    require(signature(result['rebuilt']) == signature(prior['after_child_save']), 'cold default geometry or mate ownership differs')


def native_phase(packet, trial_sha, role, gate_sha=None):
    root, job, source, pair, prediction, states = context(packet, trial_sha)
    display.previous(root, trial_sha, 'Preflight')
    display.previous(root, trial_sha, 'ControlBefore')
    preflight_sha = digest(root / 'Inspection/Preflight/Record.json')
    editing = role == 'Author'
    revision_paths = snapshots(root, pair)
    target = root / 'Inspection' / role
    target.mkdir()
    gate = prior = None
    if editing:
        require(not any(path.exists() for path in revision_paths.values()), 'the private revisions must be unused')
    else:
        gate, prior = wire_gate(root, trial_sha, gate_sha, pair)
        stage_receipt = json.loads((root / 'Inspection' / f'Stage{role}.json').read_bytes())
        expect = {'parent': gate['artifact_sha256']['parent'], 'child': gate['artifact_sha256'][role]}
        require(stage_receipt == {'trial_sha256': trial_sha, 'gate_sha256': gate_sha, 'lane': role, 'working_hashes': expect,
                                  'native_launches': 0, 'passed': True} and display.file_hashes(pair) == expect,
                'the exact lane was not staged')
    from AuthorCurves import CurveAuthor, Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    import Swapp

    rec = Recorder(target / 'Record.json', {'phase': role, 'packet_sha256': trial_sha})
    result = {'role': role, 'passed': False, 'started_at': time.time(), 'gate_sha256': gate_sha,
              'preflight_sha256': preflight_sha, 'requested_open_path': str(pair[0])}
    controller = None
    with AssemblyLoadMonitor() as monitor:
        try:
            rec.call('require idle owned Windows oracle', Swapp.sweep)
            controller = rec.call('start fresh SOLIDWORKS', Swapp.Sw)
            identity = rec.call('verify exact SOLIDWORKS 2026 SP05.2', application_identity, controller.app)
            require(identity['sha256'] == ORACLE and identity['version_matches'] and identity['file_version'] == '34.5.2.0604'
                    and identity['pe_machine'] == '0x8664' and controller.revision == '34.5.2', 'unexpected oracle build')
            result['oracle_identity'] = identity
            author = CurveAuthor(controller.app, rec, Swapp)
            require(int(author.get(controller.app, 'GetDocumentCount')) == 0
                    and author.get(controller.app, 'GetUserPreferenceToggle', 18) is True, 'ordinary cold oracle state is required')
            if editing:
                result['copy'] = display.copy_pair(author, controller.app, source, pair, job)
                context(packet, trial_sha)
            result['stored_child_reference'] = display.stored_dependency(author, controller.app, pair)
            result['files_on_open'] = display.file_hashes(pair)
            if not editing:
                require(result['files_on_open'] == expect and PureWindowsPath(result['stored_child_reference']) ==
                        PureWindowsPath(gate['saved_child_locator']), 'actual cold dependency or input bytes differ')
            model, errors, warnings = rec.call('open the one fixed owned parent path', controller.open, pair[0], read_only=not editing)
            result['open_status'] = [errors, warnings]
            require(model is not None, 'native open returned no document')
            result['returned_parent_path'] = str(author.get(model, 'GetPathName'))
            require(errors == 0 and warnings in ((0,) if editing else (0, 32)) and same_file(result['returned_parent_path'], pair[0])
                    and author.get(model, 'IsOpenedReadOnly') is (not editing), 'native open status or actual parent custody differs')
            assembly = author.typed(model, 'AssemblyDoc')
            config = author.typed(author.get(model, 'GetActiveConfiguration'), 'Configuration')
            manager = author.typed(author.get(model, 'ConfigurationManager'), 'ConfigurationManager')
            require(author.get(manager, 'LinkDisplayStatesToConfigurations') is False, 'the original unlinked display policy differs')
            if editing:
                display.inventory(author, config, [states[0][0]], states[0][0])
                finish_author(author, model, config, assembly, pair, prediction, states, result, target, revision_paths)
            else:
                finish_diagnostic(author, model, config, assembly, pair, prediction, states, result, prior, gate, role)
            require(author.get(controller.app, 'GetUserPreferenceToggle', 18) is True
                    and author.get(manager, 'LinkDisplayStatesToConfigurations') is False, 'native settings changed')
            result['passed'] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result['controller_diagnostics'] = controller.diagnostics
                except Exception as error:
                    rec.failure(error, cleanup=True)
    try:
        context(packet, trial_sha)
        require(digest(root / 'Inspection/Preflight/Record.json') == preflight_sha, 'preflight changed during native phase')
        if result['passed']:
            hashes = result['revision_sha256'] if editing else gate['artifact_sha256']
            for key, path in revision_paths.items():
                checked(path, hashes[key])
            checked(pair[0], hashes['parent'])
            checked(pair[1], hashes['Synchronized' if editing else role])
        result['immutable_inputs_unchanged'] = True
    except Exception as error:
        rec.failure(error, cleanup=True)
    result.update(finished_at=time.time(), numeric_checks=len(rec.data['checks']), first_failure=rec.data['first_failure'],
                  dialogs=monitor.log, progress_windows=monitor.progress)
    result['passed'] = bool(result['passed'] and result.get('immutable_inputs_unchanged') and not result['first_failure']
                            and not result['dialogs'] and not result.get('controller_diagnostics'))
    if not editing:
        result['zero_warning_passed'] = result['passed'] and result.get('open_status') == [0, 0]
    rec.data.update(result=result, passed=result['passed'])
    rec.flush()
    return result['passed']


def summary(packet, trial_sha, gate_sha):
    root, _, _, pair, _, _ = context(packet, trial_sha)
    gate, _ = wire_gate(root, trial_sha, gate_sha, pair)
    phases = {role: display.phase_record(root, trial_sha, role) for role in ROLES}
    left, right = (phases[key] for key in ('ControlBefore', 'ControlAfter'))
    healthy = bool(left and right and left['passed'] and right['passed'] and signature(left['initial']) == signature(right['initial'])
                   and left['observed'] == right['observed'])
    births = [row['oracle_identity']['process_creation_filetime'] for row in phases.values() if row and 'oracle_identity' in row]
    complete = bool(healthy and all(row and row['passed'] for row in phases.values()) and len(births) == len(ROLES)
                    and all(first < second for first, second in zip(births, births[1:])))
    stale, synced = (phases[key] for key in LANES)
    if complete:
        require(all(row['gate_sha256'] == gate_sha and row['files_on_open']['parent'] == gate['artifact_sha256']['parent']
                    for row in (stale, synced)) and all(row['preflight_sha256'] == digest(root / 'Inspection/Preflight/Record.json')
                    for row in phases.values()), 'finished phases used a different packet or parent')
        require(all(PureWindowsPath(stale['before_rebuild'][key]['path']) == PureWindowsPath(synced['before_rebuild'][key]['path'])
                    for key in ('parent', 'child')) and stale['requested_open_path'] == synced['requested_open_path']
                and stale['stored_child_reference'] == synced['stored_child_reference'], 'the cold paths were not fixed')
        checked(pair[1], gate['artifact_sha256']['Synchronized'])
    output = root / 'Result.json'
    require(not output.exists(), 'the packet already has a summary')
    write_json(output, {'schema': GATE_SCHEMA, 'trial_sha256': trial_sha, 'gate_sha256': gate_sha, 'controls_healthy': healthy,
                        'native_processes': len(set(births)), 'diagnostic_completed': complete,
                        'warning_cleared_after_child_save': complete and stale['open_status'] == [0, 32] and synced['zero_warning_passed'],
                        'synchronized_zero_warning_readback': complete and synced['zero_warning_passed'],
                        'all_native_opens_zero_warning': complete and all(phases[key]['zero_warning_passed'] for key in LANES),
                        'production_acceptance': False, 'stream_precedence_measured': False, 'phases': phases})
    return complete


def main():
    parser = argparse.ArgumentParser(description='Run one role in the fixed-parent D01 child-save experiment')
    sub = parser.add_subparsers(dest='mode', required=True)
    for command in ('preflight', 'control', 'author', 'stage', 'observe', 'summary'):
        mode = sub.add_parser(command)
        if command == 'control':
            mode.add_argument('side', choices=('before', 'after'))
        if command in ('stage', 'observe'):
            mode.add_argument('lane', choices=('stale', 'synchronized'))
        mode.add_argument('packet', type=Path)
        mode.add_argument('trial_sha')
        if command in ('stage', 'observe', 'summary'):
            mode.add_argument('gate_sha')
    args = parser.parse_args()
    if args.mode == 'preflight':
        context(args.packet, args.trial_sha)
        passed = display.preflight(args.packet, args.trial_sha)
    elif args.mode == 'control':
        context(args.packet, args.trial_sha)
        passed = display.run_phase(args.packet, args.trial_sha, 'Control' + args.side.title())
    elif args.mode == 'author':
        passed = native_phase(args.packet, args.trial_sha, 'Author')
    elif args.mode == 'stage':
        passed = stage(args.packet, args.trial_sha, args.lane.title(), args.gate_sha)
    elif args.mode == 'observe':
        passed = native_phase(args.packet, args.trial_sha, args.lane.title(), args.gate_sha)
    else:
        passed = summary(args.packet, args.trial_sha, args.gate_sha)
    print(json.dumps({'mode': args.mode, 'diagnostic_step_completed': passed}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
