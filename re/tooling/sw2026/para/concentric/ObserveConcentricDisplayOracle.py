from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


sys.path.insert(0, str(Path(__file__).resolve().parent))

from ConcentricApiMetadata import LIBRARIES
from ConcentricNativeContract import ORACLE, checked, close_numbers, digest, require, signature, validate_prediction, write_json
from InspectGeneratedConcentric import capture, input_path, same_file
from ObserveConcentricPersistence import ensure_runtime, phase_record


SCHEMA = 'kit.sw2026.concentric-display-oracle.v1'
ROLES = ('ControlBefore', 'Author', 'Observe', 'ControlAfter')
SIDES = ('parent', 'child')
MEMBERS = {
    'IConfiguration': {
        'CreateDisplayState': (1, 1), 'ApplyDisplayState': (1, 1), 'GetDisplayStates': (1, 0),
        'GetDisplayStatesCount': (1, 0), 'GetDisplayStateComponentVisibility': (1, 4),
    },
    'IConfigurationManager': {'LinkDisplayStatesToConfigurations': (2, 0)},
    'IComponent2': {'Visible': (2, 0), 'IsHidden': (1, 1), 'IsSuppressed': (1, 0), 'GetID': (1, 0)},
    'IModelDoc2': {'IsOpenedReadOnly': (1, 0), 'Save3': (1, 3)},
    'ISldWorks': {'CopyDocument': (1, 5), 'GetDocumentDependencies2': (1, 4)},
}
ENUMS = {
    'swComponentVisibilityState_e': {'swComponentHidden': 0, 'swComponentVisible': 1},
    'swMoveCopyError_e': {'swMoveCopyErrorNone': 0},
    'swMoveCopyOptions_e': {'swMoveCopyOptionsOverwriteExistingDocs': 1, 'swMoveCopyOptionsCreateNewFolder': 2},
}


def owned_paths(root, job):
    folder = root / 'Working'
    require(folder.resolve() == folder and folder.is_dir() and not folder.is_symlink() and not folder.is_junction(),
            'the dedicated working directory was redirected')
    return tuple(folder / job['working_names'][side] for side in SIDES)


def verify(packet, expected):
    packet = checked(packet, expected).resolve()
    root = packet.parent
    job = json.loads(packet.read_bytes())
    require(job['schema'] == SCHEMA and job['oracle_sha256'] == ORACLE and job['heldout_inputs_read'] == 0
            and job['native_processes_started'] == 0 and job['require_preference_18_true'] is True,
            'the exact disclosed display packet is required')
    require(packet == Path(job['guest_root']) / 'Trial.json' and Path(__file__).resolve() == root / 'Tools' / Path(__file__).name,
            'run the frozen observer from its managed guest packet')
    for relative, wanted in job['files_sha256'].items():
        path = root / relative
        require(path.resolve() == path and path.parent in (root / 'Tools', root / 'Evidence'), 'invalid frozen path')
        checked(path, wanted)
    ensure_runtime(root)
    require(set(job['controls']) == set(job['working_names']) == set(SIDES), 'exactly one parent and one part are required')
    source = tuple(checked(input_path(job['controls'][side]), job['controls'][side]['sha256']) for side in SIDES)
    require(all(path.resolve() == path for path in source) and source[0].parent == source[1].parent
            and tuple(job['working_names'][side] for side in SIDES) == tuple(path.name for path in source),
            'the ordinary linked control locators differ')
    working = owned_paths(root, job)
    require(not working[0].parent.samefile(source[0].parent), 'working and source directories must be separate')
    prediction = validate_prediction(json.loads((root / 'Evidence/Prediction.json').read_bytes()))
    states = tuple((row['name'], tuple(row['visibility'])) for row in job['states'])
    require(len(states) == 3 and len({name.casefold() for name, _ in states}) == 3
            and tuple(vector for _, vector in states) == ((1, 1), (1, 0), (0, 1)), 'named visibility intent differs')
    return root, job, source, working, prediction, states


def metadata():
    import pythoncom

    pythoncom.CoInitialize()
    try:
        libraries = {name: pythoncom.LoadRegTypeLib(guid, 34, 0, 0) for name, guid in LIBRARIES.items()}
        require(all(tuple(lib.GetLibAttr()[3:5]) == (34, 0) for lib in libraries.values()), 'both 2026 COM libraries are required')
        interfaces, enums = {}, {}
        for family, library in libraries.items():
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                attrs = info.GetTypeAttr()
                if family == 'sldworks' and name in MEMBERS:
                    members = []
                    for ordinal in range(attrs.cFuncs):
                        entry = info.GetFuncDesc(ordinal)
                        names = list(info.GetNames(entry.memid))
                        if names and names[0] in MEMBERS[name]:
                            members.append({'names': names, 'member_id': entry.memid, 'kind': entry.invkind,
                                            'arguments': repr(entry.args), 'result': repr(entry.rettype)})
                    interfaces[name] = {'guid': str(attrs[0]), 'members': members}
                if family == 'swconst' and name in ENUMS:
                    values = {}
                    for ordinal in range(attrs.cVars):
                        entry = info.GetVarDesc(ordinal)
                        member = info.GetNames(entry.memid)[0]
                        if member in ENUMS[name]:
                            values[member] = entry.value
                    enums[name] = values
        for name, wanted in MEMBERS.items():
            rows = interfaces.get(name, {}).get('members', [])
            for member, (kind, count) in wanted.items():
                require(any(row['names'][0] == member and row['kind'] == kind and len(row['names']) == count + 1
                            for row in rows), f'registered prerequisite differs: {name}.{member}')
        require(any(row['names'][0] == 'Visible' and row['kind'] == 4 for row in interfaces['IComponent2']['members']),
                'the registered component visibility setter is required')
        require(enums == ENUMS, 'registered enum values differ from the frozen authoring protocol')
        return {'libraries': {name: {'guid': str(lib.GetLibAttr()[0]), 'major': 34, 'minor': 0}
                              for name, lib in libraries.items()}, 'interfaces': interfaces, 'enums': enums}
    finally:
        pythoncom.CoUninitialize()


def preflight(packet, expected):
    root, _, _, working, _, _ = verify(packet, expected)
    require(not list(working[0].parent.iterdir()), 'the working directory must be empty before preflight')
    from AuthorCurves import Recorder

    target = root / 'Inspection' / 'Preflight'
    target.mkdir()
    rec = Recorder(target / 'Record.json', {'phase': 'Preflight', 'packet_sha256': expected})
    try:
        api = rec.call('inspect registered API declarations without CAD activation', metadata)
        rec.data.update(result={'passed': True, 'api': api, 'native_launches': 0}, passed=True)
    except Exception as error:
        rec.failure(error)
    rec.flush()
    return rec.data['passed']


def previous(root, expected, role):
    result = phase_record(root, expected, role)
    require(result and result.get('passed') is True, f'{role} must pass first')
    return result


def stored_dependency(author, app, pair):
    parent, child = pair
    refs = tuple(author.get(app, 'GetDocumentDependencies2', str(parent), False, False, False) or ())
    labels = (child.stem.casefold(), child.name.casefold())
    require(len(refs) == 2 and refs[0].casefold() in labels and same_file(refs[1], child),
            'the stored parent dependency does not resolve to its exact paired child')
    return refs[1]


def copy_pair(author, app, source, working, job):
    require(not list(working[0].parent.iterdir()), 'the native copy destination must be empty')
    require(int(author.get(app, 'GetDocumentCount')) == 0, 'native copy requires every document closed')
    original_ref = stored_dependency(author, app, source)
    sw = author.sw
    kind = sw.pythoncom.VT_ARRAY | sw.pythoncom.VT_BSTR
    status = author.rec.call('CopyDocument with only the pinned original child mapped to the owned copy', sw.invoke, app,
                             'CopyDocument', str(source[0]), str(working[0]), sw.VARIANT(kind, [original_ref]),
                             sw.VARIANT(kind, [str(working[1])]), 0,
                             parameters={'source': list(map(str, source)), 'destination': list(map(str, working)),
                                         'stored_reference': original_ref, 'copy_options': 0})
    require(type(status) is int and status == 0 and all(path.is_file() and path.resolve() == path for path in working)
            and all(not path.samefile(origin) for origin, path in zip(source, working, strict=True))
            and int(author.get(app, 'GetDocumentCount')) == 0, 'vendor copy failed or selected an unowned file')
    hashes = file_hashes(working)
    require(hashes['child'] == job['controls']['child']['sha256'], 'vendor copy changed the disclosed child bytes')
    return {'status': status, 'original_reference': original_ref, 'files_sha256': hashes}


def file_hashes(paths):
    return {side: digest(path) for side, path in zip(SIDES, paths, strict=True)}


def inventory(author, config, wanted, active):
    names = tuple(author.get(config, 'GetDisplayStates') or ())
    require(len(names) == int(author.get(config, 'GetDisplayStatesCount')) == len(wanted)
            and set(names) == set(wanted) and names[0] == active, 'display names, count or active state differ')
    return list(names)


def apply(author, config, name):
    require(author.get(config, 'ApplyDisplayState', name) is True, f'failed to activate display state {name}')


def native_component(author, raw):
    if not hasattr(raw, '_oleobj_'):
        raw = author.sw.wc.Dispatch(raw)
    return author.typed(raw, 'Component2')


def ownership(author, component, child_path, expected):
    name = str(author.get(component, 'Name2'))
    require(name in expected and same_file(author.get(component, 'GetPathName'), child_path),
            'display row selected another occurrence or child path')
    native_id = int(author.get(component, 'GetID'))
    require(native_id == expected[name]['native_id'] and not author.get(component, 'IsSuppressed'),
            'display row changed an occurrence ID or suppression')
    return name, native_id


def named_visibility(author, config, state, child_path, expected):
    name, vector = state
    sw = author.sw
    members = sw.VARIANT(sw.pythoncom.VT_BYREF | sw.pythoncom.VT_VARIANT, None)
    values = author.get(config, 'GetDisplayStateComponentVisibility', name, False, True, members)
    codes = tuple(values or ())
    returned = tuple(members.value or ())
    require(len(codes) == len(returned) == len(vector) and all(type(code) is int and code in (0, 1) for code in codes),
            f'named visibility returned incomplete or unknown values for {name}')
    rows = {}
    for code, raw in zip(codes, returned, strict=True):
        occurrence, native_id = ownership(author, native_component(author, raw), child_path, expected)
        require(occurrence not in rows, 'duplicate named visibility member')
        rows[occurrence] = {'native_id': native_id, 'visible': code}
    require(tuple(rows[occurrence]['visible'] for occurrence in expected) == vector,
            f'named visibility differs for {name}')
    return rows


def live_visibility(author, assembly, child_path, expected, state):
    name, vector = state
    members = author.get(assembly, 'GetComponents', True) or ()
    require(len(members) == len(expected) == int(author.get(assembly, 'GetComponentCount', False)),
            'the two direct resolved components are required in every display state')
    objects, rows = {}, {}
    for raw in members:
        component = native_component(author, raw)
        occurrence, native_id = ownership(author, component, child_path, expected)
        require(occurrence not in objects, 'duplicate live display member')
        baseline = expected[occurrence]
        visible = author.get(component, 'Visible')
        hidden = author.get(component, 'IsHidden', False)
        transform = author.typed(author.get(component, 'Transform2'), 'MathTransform')
        loaded = author.get(component, 'GetModelDoc2')
        require(type(visible) is int and visible in (0, 1) and hidden is (visible == 0)
                and loaded is not None and same_file(author.get(loaded, 'GetPathName'), child_path)
                and str(author.get(component, 'ReferencedConfiguration')) == baseline['configuration']
                and bool(author.get(component, 'IsFixed')) is baseline['fixed']
                and close_numbers(author.get(transform, 'ArrayData'), baseline['transform'], relative=1e-9, absolute=1e-12),
                'live display transition changed resolved ownership, placement or visibility semantics')
        objects[occurrence] = component
        rows[occurrence] = {'native_id': native_id, 'visible': visible, 'hidden': hidden}
    require(tuple(rows[occurrence]['visible'] for occurrence in expected) == vector,
            f'active visibility differs for {name}')
    return objects, rows


def read_states(author, model, config, assembly, child_path, expected, states, activation):
    default = states[0]
    names = tuple(name for name, _ in states)
    order_at_default = inventory(author, config, names, default[0])
    named = {name: named_visibility(author, config, (name, vector), child_path, expected) for name, vector in states}
    active = {}
    for state in (*activation, default):
        name, _ = state
        apply(author, config, name)
        active_order = inventory(author, config, names, name)
        _, live = live_visibility(author, assembly, child_path, expected, state)
        require(all(row['visible'] == named[name][occurrence]['visible'] for occurrence, row in live.items()),
                'activated and separately queried state visibility disagree')
        require(int(author.get(author.get(model, 'Extension'), 'GetWhatsWrongCount')) == 0,
                'the active state reported native diagnostics')
        active[name] = {'live': live, 'active_order': active_order}
    return {'named': named, 'activated': active, 'inventory_with_default_active': order_at_default}


def save_parent(author, model, working, child_sha):
    parent, child = working
    require(same_file(author.get(model, 'GetPathName'), parent) and not author.get(model, 'IsOpenedReadOnly'),
            'only the owned writable assembly may be saved')
    author.get(model, 'SetSaveFlag')
    sw = author.sw
    errors, warnings = sw.byref_long(), sw.byref_long()
    result = author.rec.call('save only the owned assembly at the same native path', sw.invoke, model,
                             'Save3', sw.SAVE_SILENT, errors, warnings)
    status = [bool(result), int(errors.value), int(warnings.value)]
    hashes = file_hashes(working)
    require(status == [True, 0, 0] and hashes['child'] == child_sha and child.is_file(),
            'native display save warned, failed or changed the linked child')
    return {'status': status, 'files_sha256': hashes}


def author_states(author, model, config, assembly, working, prediction, expected, states, result, target):
    default, *created = states
    child_sha = result['files_on_open']['child']
    before = save_parent(author, model, working, child_sha)
    snapshot = target / 'Before.SLDASM'
    with snapshot.open('xb') as stream:
        stream.write(checked(working[0], before['files_sha256']['parent']).read_bytes())
    require(digest(snapshot) == before['files_sha256']['parent'], 'same-destination baseline snapshot differs')
    result['before_authoring'] = before | {'snapshot': str(snapshot)}
    known_names = [default[0]]
    for state in created:
        name, vector = state
        apply(author, config, default[0])
        inventory(author, config, known_names, default[0])
        live_visibility(author, assembly, working[1], expected, default)
        require(author.get(config, 'CreateDisplayState', name) is True, f'failed to create {name} independently from the default')
        known_names.append(name)
        apply(author, config, name)
        inventory(author, config, known_names, name)
        components, _ = live_visibility(author, assembly, working[1], expected, (name, default[1]))
        for occurrence, code in zip(expected, vector, strict=True):
            author.set(components[occurrence], 'Visible', code)
        live_visibility(author, assembly, working[1], expected, state)
    apply(author, config, default[0])
    result['before_save'] = read_states(author, model, config, assembly, working[1], expected, states, created)
    require(author.get(model, 'ForceRebuild3', False) is True, 'authored assembly failed its all-visible rebuild')
    rebuilt, _ = capture(author, model, assembly, working[1], prediction)
    require(signature(rebuilt) == signature(result['initial']), 'authoring changed source geometry or owned mate identities')
    result['rebuilt'] = rebuilt
    result['saved'] = save_parent(author, model, working, child_sha)
    require(result['saved']['files_sha256']['parent'] != before['files_sha256']['parent'], 'the owned parent save did not change')
    result['observed'] = read_states(author, model, config, assembly, working[1], expected, states, created)


def run_phase(packet, expected, role):
    root, job, source, working, prediction, states = verify(packet, expected)
    previous(root, expected, 'Preflight')
    prior_preflight = digest(root / 'Inspection/Preflight/Record.json')
    editing = role == 'Author'
    observing = role == 'Observe'
    control = not editing and not observing
    pair = source if control else working
    if editing:
        previous(root, expected, 'ControlBefore')
    prior = previous(root, expected, 'Author') if observing else None
    if observing:
        for side, path in zip(SIDES, pair, strict=True):
            checked(path, prior['saved']['files_sha256'][side])
        checked(root / 'Inspection/Author/Before.SLDASM', prior['before_authoring']['files_sha256']['parent'])
    target = root / 'Inspection' / role
    target.mkdir()

    import Swapp
    from AuthorCurves import CurveAuthor, Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    rec = Recorder(target / 'Record.json', {'phase': role, 'packet_sha256': expected})
    result = {'role': role, 'preflight_sha256': prior_preflight, 'passed': False, 'started_at': time.time()}
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
            require(int(author.get(controller.app, 'GetDocumentCount')) == 0, 'the oracle is not cold')
            require(author.get(controller.app, 'GetUserPreferenceToggle', 18) is True, 'ordinary occurrence naming preference is required')
            if editing:
                result['copy'] = copy_pair(author, controller.app, source, working, job)
                verify(packet, expected)
            if not control:
                result['stored_child_reference'] = stored_dependency(author, controller.app, pair)
            result['files_on_open'] = file_hashes(pair)
            model, errors, warnings = rec.call('open exact linked pair', controller.open, pair[0], read_only=not editing)
            result['open_status'] = [errors, warnings]
            require(model is not None and errors == warnings == 0 and same_file(author.get(model, 'GetPathName'), pair[0])
                    and author.get(model, 'IsOpenedReadOnly') is (not editing), 'native open warned, failed or selected an unexpected path or access mode')
            assembly = author.typed(model, 'AssemblyDoc')
            config = author.typed(author.get(model, 'GetActiveConfiguration'), 'Configuration')
            manager = author.typed(author.get(model, 'ConfigurationManager'), 'ConfigurationManager')
            result['link_display_states_to_configurations'] = author.get(manager, 'LinkDisplayStatesToConfigurations')
            default = states[0]
            expected_states = states if observing else (default,)
            result['opening_display_states'] = inventory(author, config, [name for name, _ in expected_states], default[0])
            require(author.get(model, 'ForceRebuild3', False) is True, 'native all-visible baseline rebuild failed')
            result['initial'], _ = capture(author, model, assembly, pair[1], prediction)
            occurrences = {row['name']: row for row in result['initial']['occurrences']}
            if control:
                require([row['native_id'] for row in occurrences.values()] == job['expected_original_ids'], 'the original owner IDs differ')
            if editing:
                author_states(author, model, config, assembly, working, prediction, occurrences, states, result, target)
            else:
                activation = tuple(reversed(states[1:])) if observing else ()
                result['observed'] = read_states(author, model, config, assembly, pair[1], occurrences, expected_states, activation)
                if observing:
                    require(signature(result['initial']) == signature(prior['rebuilt'])
                            and result['observed']['named'] == prior['observed']['named'], 'cold save readback changed native identities or named visibility')
                    require(author.get(model, 'ForceRebuild3', False) is True, 'restored default failed to rebuild')
                    rebuilt, _ = capture(author, model, assembly, pair[1], prediction)
                    require(signature(rebuilt) == signature(result['initial']), 'after switching, reopened identities differ')
                    result['rebuilt'] = rebuilt
            require(author.get(manager, 'LinkDisplayStatesToConfigurations') is result['link_display_states_to_configurations'],
                    'the document display-link policy changed')
            require(author.get(controller.app, 'GetUserPreferenceToggle', 18) is True, 'the ordinary naming preference changed')
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
        verify(packet, expected)
        require(digest(root / 'Inspection/Preflight/Record.json') == prior_preflight, 'preflight receipt changed during the phase')
        if result['passed']:
            wanted = result['saved']['files_sha256'] if editing else result['files_on_open']
            require(file_hashes(pair) == wanted, 'archive bytes differed after the owned process closed')
        result['frozen_inputs_unchanged'] = True
    except Exception as error:
        rec.failure(error, cleanup=True)
    result.update(finished_at=time.time(), numeric_checks=len(rec.data['checks']), unclassified_dialogs=monitor.log,
                  progress_windows=monitor.progress, first_failure=rec.data['first_failure'])
    result['passed'] = bool(result['passed'] and not result['first_failure'] and not result['unclassified_dialogs']
                            and not result.get('controller_diagnostics') and result.get('frozen_inputs_unchanged'))
    rec.data.update(result=result, passed=result['passed'])
    rec.flush()
    return result['passed']


def summarize(packet, expected):
    root, _, _, working, _, _ = verify(packet, expected)
    phases = {role: phase_record(root, expected, role) for role in ROLES}
    completed = all(row and row['passed'] for row in phases.values())
    left, right = phases['ControlBefore'], phases['ControlAfter']
    healthy = bool(left and right and left['passed'] and right['passed']
                   and signature(left['initial']) == signature(right['initial']) and left['observed'] == right['observed'])
    births = [row['oracle_identity']['process_creation_filetime'] for row in phases.values() if row and 'oracle_identity' in row]
    passed = bool(completed and healthy and len(births) == 4 and all(a < b for a, b in zip(births, births[1:])))
    if passed:
        preflight_sha = digest(root / 'Inspection/Preflight/Record.json')
        policies = {row['link_display_states_to_configurations'] for row in phases.values()}
        saved = phases['Author']['saved']['files_sha256']
        checked(root / 'Inspection/Author/Before.SLDASM', phases['Author']['before_authoring']['files_sha256']['parent'])
        passed = bool(len(policies) == 1 and all(row['preflight_sha256'] == preflight_sha for row in phases.values())
                      and file_hashes(working) == saved)
    summary = root / 'Result.json'
    require(not summary.exists(), 'the packet already has a summary')
    write_json(summary, {'schema': SCHEMA, 'packet_sha256': expected, 'scope': 'native disclosed visibility discovery',
                         'passed': passed, 'controls_healthy': healthy, 'distinct_native_processes': len(set(births)),
                         'heldout_inputs_read': 0, 'heldout_acceptance': False, 'stream_precedence_measured': False,
                         'phases': phases})
    return passed


def main():
    parser = argparse.ArgumentParser(description='Run one frozen D01 display-state discovery phase')
    modes = parser.add_subparsers(dest='mode', required=True)
    for name in ('preflight', 'control', 'author', 'observe', 'summary'):
        mode = modes.add_parser(name)
        if name == 'control':
            mode.add_argument('side', choices=('before', 'after'))
        mode.add_argument('packet', type=Path)
        mode.add_argument('sha256')
    args = parser.parse_args()
    if args.mode == 'preflight':
        passed = preflight(args.packet, args.sha256)
    elif args.mode == 'summary':
        passed = summarize(args.packet, args.sha256)
    else:
        phase = 'Control' + args.side.title() if args.mode == 'control' else args.mode.title()
        passed = run_phase(args.packet, args.sha256, phase)
    print(json.dumps({'mode': args.mode, 'passed': passed}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
