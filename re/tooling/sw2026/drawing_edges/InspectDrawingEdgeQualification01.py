from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys
import time

from DrawingEdgeState01 import require, vector


SCHEMA = 'kit.sw2026.drawing-edge-qualification.v1'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
WRAPPER = 'd8982a8caef31e4c62ed49b70d3747f701fee0622bbaec7a550d6e874327e959'
API_METADATA = '92235db40b63b95246f2479a9166ecaa12c242d3f96d149e13827d1e92b756f5'
COMPONENT_METADATA = 'bd66c956040c0547d1f0b7f5bd35e80681e9910542ccf0e9a61dcd79d34daa24'
TOOLS = {'InspectDrawingEdgeQualification01.py', 'DrawingEdgeState01.py', 'AuthorCurves.py', 'AuthorDrawingSources.py',
         'InspectDrawingCache.py', 'DrawingCacheCases.py', 'Swapp.py', 'OracleIdentity.py', 'DrawingEdgeBody01.py'}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def checked(root, relative, expected):
    target = (root / relative).resolve(strict=True)
    require(target.is_relative_to(root) and target.is_file() and digest(target) == expected, 'frozen packet file differs: ' + relative)
    return target


def prism(case):
    lower = vector(case['prism_m']['minimum'], 3)
    upper = vector(case['prism_m']['maximum'], 3)
    require(lower[2] == 0 and all(a < b for a, b in zip(lower, upper, strict=True)), 'ordinary Front prism requires a positive blind depth from z=0')
    sizes = [b - a for a, b in zip(lower, upper, strict=True)]
    width, height, depth = sizes
    points = [vector(item, 3) for item in case['edge_endpoints_m']]
    require(len(points) == 2 and all(math.isclose(point[0], lower[0], abs_tol=1e-12) and point[2] == upper[2] for point in points)
            and sorted(point[1] for point in points) == [lower[1], upper[1]], 'select only the camera-facing Front cap left boundary rail derived from actual prism bounds')
    expected = case['expected']
    view = expected['view']
    require(view['orientation'] == '*Front' and view['scale'] == 1 and view['configuration']
            and len(view['model_to_view']) == 16, 'the trial admits only one explicit Front unit-scale view')
    require(view['model_to_view'][:9] == [1, 0, 0, 0, 1, 0, 0, 0, 1] and view['model_to_view'][12] == 1,
            'Front edge prediction requires the proved canonical model-to-view rotation')
    prediction = {'volume_m3': width * height * depth, 'area_m2': 2 * (width * height + width * depth + height * depth),
                  'center_m': [(a + b) / 2 for a, b in zip(lower, upper, strict=True)]}
    for field, value in [('child_volume_m3', prediction['volume_m3']), ('child_area_m2', prediction['area_m2'])]:
        require(math.isclose(view[field], value, rel_tol=2e-12, abs_tol=1e-15), 'expected child geometry is not derived from the neutral prism')
    require(all(math.isclose(a, b, rel_tol=2e-12, abs_tol=1e-15) for a, b in zip(view['child_center_m'], prediction['center_m'], strict=True)), 'child centre does not match neutral analytic prism')
    annotation = case['annotation']
    require(annotation['before_text'] != annotation['after_text'] and all(isinstance(annotation[key], str) and 0 < len(annotation[key]) <= 32 for key in ('before_text', 'after_text')), 'annotation requires distinct explicit short texts')
    positions = [vector(annotation[key], 3) for key in ('before_position_m', 'after_position_m')]
    require(positions[0] != positions[1] and all(p[2] == 0 for p in positions), 'annotation edit requires two distinct sheet-plane points')
    return prediction


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    request = json.loads(checked(root, packet.name, expected).read_bytes())
    require(request['schema'] == SCHEMA and request['oracle_sha256'] == ORACLE and request['heldout_inputs_read'] == 0,
            'unexpected disclosed edge qualification packet')
    require(request['source_scope'] == 'disclosed-only' and request['native_acceptance'] is False, 'this is a measurement protocol, not acceptance')
    component_metadata = json.loads(checked(root, 'ComponentApiMetadata.json', COMPONENT_METADATA).read_bytes())
    require(component_metadata['wrapper_sha256'] == WRAPPER and component_metadata['cad_objects_created'] == 0
            and component_metadata['native_processes_started_by_tool'] == 0 and component_metadata['model_documents_opened'] == 0,
            'exact root-component API metadata is required')
    expected_component_slots = {'GetParent': 664, 'IsRoot': 1096, 'GetModelDoc2': 1104}
    for interface, values in [('IComponent2', expected_component_slots), ('IModelDoc2', {'GetType': 736})]:
        observed = component_metadata['interfaces'][interface]
        require(observed['missing'] == [], 'exact component/root-model interface metadata is incomplete')
        for member, slot in values.items():
            selected = [row for row in observed['members'] if row['names'][0] == member and row['invoke_kind'] == 1]
            require(len(selected) == 1 and selected[0]['vtable_offset_bytes'] == slot and selected[0]['arguments'] == [],
                    'exact zero-argument component/root-model API shape differs: ' + member)
    require(request['component_api_metadata_sha256'] == COMPONENT_METADATA and request['observer_revision'] == 'visible-part-body-owner-05'
            and request['previous_trial_sha256'] == '6924557cf5ddaf5013a7a7414fe65938df629c543bcdb4ea5b8ab900c216eb74'
            and request['previous_failed_result_sha256'] == '2b1086065acffae0b4bc72cc73f03b4b29e212a1914fc0d1f54e247321a4d132'
            and request['visible_edge_selection_rule'] == 'positive-view-normal-outer-cap-left-rail-v1'
            and request['original_trial_sha256'] == '36143744fc79f19fb60434d24884288f72733e764ed9fd8a8138aff4233d0872'
            and request['original_failed_result_sha256'] == '1056bde8473497d695c89276812fab2db2a66136c9c7351e8ddac40af47c6eb0',
            'the observer-only retry must preserve its exact predecessor')

    from DrawingEdgeBody01 import METADATA as BODY_METADATA, validate as validate_body_api

    body_metadata = json.loads(checked(root, 'BodyApiMetadata.json', BODY_METADATA).read_bytes())
    validate_body_api(body_metadata)
    require(request['body_api_metadata_sha256'] == BODY_METADATA
            and request['body_ownership_rule'] == 'sole-resolved-part-body-and-exact-live-edge-membership-v1',
            'the new body-ownership proof must remain exact')

    tools = root / 'Tools'
    require(Path(__file__).resolve().parent == tools and set(request['tools_sha256']) == TOOLS, 'run only the complete frozen observer')
    for name, expected_tool in request['tools_sha256'].items():
        checked(root, 'Tools/' + name, expected_tool)
    metadata = json.loads(checked(root, 'ApiMetadata.json', API_METADATA).read_bytes())
    require(metadata['wrapper_sha256'] == WRAPPER and metadata['cad_objects_created'] == 0
            and metadata['native_processes_started_by_tool'] == 0 and metadata['model_documents_opened'] == 0,
            'exact registered 2026 API metadata is required')
    require(metadata['enums']['swUserPreferenceToggle_e']['swDetailingModeSaveModelData'] == 779
            and metadata['enums']['swUserPreferenceOption_e']['swDetailingNoOptionSpecified'] == 0
            and metadata['enums']['swViewEntityType_e']['swViewEntityType_Edge'] == 1
            and metadata['enums']['swSelectType_e']['swSelEDGES'] == 1
            and metadata['enums']['swObjectEquality']['swObjectSame'] == 1,
            'exact API enum domains differ')
    require(len(request['cases']) == 2 and [c['role'] for c in request['cases']] == ['Control', 'Generated'], 'one pristine control and one generated disclosed pair are required')
    for case in request['cases']:
        prism(case)
        require(case['provenance_sha256'] and case['approved_child_paths'], 'explicit pair provenance and physical child paths are required')
        for label in ('drawing', 'part'):
            source = checked(root, case[label + '_source'], case[label + '_sha256'])
            require(source.stat().st_size == case[label + '_bytes'], 'frozen native input length differs')
        require(all(PureWindowsPath(path).is_absolute() for path in case['approved_child_paths']), 'approved child identities must be absolute Windows paths')
        require(case['expected']['view']['resolved_reference_path'] in case['approved_child_paths'], 'expected real child path is not approved')
        if case.get('drawing_target') is not None:
            require(case['role'] == 'Generated' and PureWindowsPath(case['drawing_target']).is_absolute()
                    and PureWindowsPath(case['part_target']).is_absolute()
                    and PureWindowsPath(case['drawing_target']).parent == PureWindowsPath(case['part_target']).parent,
                    'generated drawing and child require exact paired encoded paths')
    return request


def live_check(author, drawing, case, expected_tree):
    import AuthorDrawingSources as sources
    from DrawingEdgeState01 import model_view
    from InspectDrawingCache import drawing_tree

    view, child, child_path = model_view(author, drawing, case)
    request = {key: case['expected']['view'][key] for key in ('orientation', 'position_m', 'scale')}
    actual = sources.snapshot(author, author.model, drawing, request, child_path, case['expected']['sheet_properties'][0])
    expected = {**case['expected'], 'view': {**case['expected']['view'], 'resolved_reference_path': str(child_path)}}
    sources.compare_states(author, actual, expected)
    rows = drawing_tree(author)
    require(expected_tree is None or rows == expected_tree, 'complete drawing feature tree differs')
    child_rows = author.rec.call('complete linked child history', author.sw.features, child)
    require(all(row.get('error') == 0 and row.get('warning') is False and row.get('suppressed') is False for row in child_rows), 'actual child has feature errors, warnings or suppression')
    if case.get('child_tree') is not None:
        require([[row['name'], row['type']] for row in child_rows] == case['child_tree'], 'complete linked child history differs from neutral presentation')
    part = author.typed(child, 'PartDoc')
    require(len(author.get(part, 'GetBodies2', 0, False) or ()) == 1, 'actual child must have one real solid body')
    for name, value in case.get('child_parameters_m', {}).items():
        parameter = author.get(child, 'Parameter', name)
        require(parameter is not None and author.get(parameter, 'DrivenState') == 2 and not author.get(parameter, 'ReadOnly'), 'actual child driver is absent, driven or read only')
        author.rec.close_number(name, author.get(parameter, 'SystemValue'), value)
    return {'drawing': actual, 'drawing_tree': rows, 'child_tree': child_rows}


def phase(packet, packet_sha, case, directory, source, source_sha, *, prior=None, expected_tree=None):
    import AuthorCurves as curves
    import Swapp
    from OracleIdentity import application_identity
    from DrawingEdgeState01 import annotation_state, create_note, find_annotation, persist_id, resolve_persist, select_edge

    directory.mkdir(parents=True, exist_ok=False)
    rec = curves.Recorder(directory / 'Record.json', {'case': case['role'], 'reopen': prior is not None})
    result = {'passed': False, 'native_acceptance': False}
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            verify(packet, packet_sha)
            require(digest(source) == source_sha, 'native drawing changed before open')
            rec.call('idle native application guard', Swapp.sweep)
            controller = rec.call('launch one owned oracle', Swapp.Sw, visible=True)
            identity = rec.call('exact native identity', application_identity, controller.app)
            result['oracle_identity'] = identity
            require(identity['version_matches'] and identity['sha256'] == ORACLE and controller.revision == '34.5.2', 'oracle build differs')
            author = curves.CurveAuthor(controller.app, rec, Swapp)
            author.edge_body_metadata = json.loads((packet.parent / 'BodyApiMetadata.json').read_bytes())
            require(digest(Path(author.interfaces.__file__)) == WRAPPER, 'registered 2026 wrapper bytes differ')
            author.model, errors, warnings = rec.call('open exact disclosed drawing', controller.open, source, doctype=3, read_only=True)
            result.update(open_errors=errors, open_warnings=warnings)
            require(author.model is not None and errors == warnings == 0, 'drawing did not open without errors and warnings')
            drawing = author.typed(author.model, 'DrawingDoc')
            tree = expected_tree if prior is None else prior['after_state']['drawing_tree']
            result['initial_state'] = live_check(author, drawing, case, tree)
            require(bool(author.get(author.model, 'ForceRebuild3', False)), 'ordinary drawing rebuild failed')
            result['rebuilt_state'] = live_check(author, drawing, case, tree)
            extension = author.typed(author.get(author.model, 'Extension'), 'ModelDocExtension')
            before = author.get(extension, 'GetUserPreferenceToggle', 779, 0)
            result['save_model_data_before'] = before
            require(type(before) is bool, 'SaveModelData did not return the documented Boolean')
            if prior is None:
                require(bool(author.get(extension, 'SetUserPreferenceToggle', 779, 0, True)), 'document SaveModelData setter refused the ordinary drawing')
            require(author.get(extension, 'GetUserPreferenceToggle', 779, 0) is True, 'document SaveModelData is not enabled')
            view, child, edge, selected = select_edge(author, drawing, case)
            result['edge_selection'] = selected
            if prior is None:
                annotation, initial = create_note(author, drawing, view, edge, case)
                result['created_annotation'] = initial
                token = persist_id(author, extension, edge)
            else:
                require(digest(Path(prior['private_state_path'])) == prior['private_state_sha256'], 'saved private observer state changed')
                private = json.loads(Path(prior['private_state_path']).read_bytes())
                token = bytes(private['edge_persist_id'])
                annotation = find_annotation(author, view, prior['annotation']['name'])
            persisted = resolve_persist(author, extension, token)
            require(author.get(author.app, 'IsSame', persisted, edge) == 1, 'persistent edge token resolved a different live edge')
            result['annotation'] = annotation_state(author, annotation, case['annotation']['after_text'], case['annotation']['after_position_m'], edge, case['edge_endpoints_m'])
            require(bool(author.get(author.model, 'ForceRebuild3', False)), 'edge annotation edit did not rebuild')
            result['after_state'] = live_check(author, drawing, case, result['rebuilt_state']['drawing_tree'])
            view, child, current_edge, _ = select_edge(author, drawing, case)
            require(author.get(author.app, 'IsSame', resolve_persist(author, extension, token), current_edge) == 1, 'persistent edge no longer matches after rebuild')
            edge = current_edge
            result['annotation_after_rebuild'] = annotation_state(author, annotation, case['annotation']['after_text'], case['annotation']['after_position_m'], edge, case['edge_endpoints_m'])
            result['persistent_edge_reference'] = {'bytes': len(token), 'sha256': sha256(token).hexdigest(), 'resolved_actual_edge': True}
            if prior is None:
                target = directory / 'AnnotatedDrawing.SLDDRW'
                require(not target.exists(), 'native output path already exists')
                author.get(author.model, 'SetSaveFlag')
                result['save_status'] = rec.call('save edge annotation', controller.save_as, author.model, target)
                require(result['save_status'] == (True, 0, 0) and target.is_file() and target.stat().st_size > 0, 'edge annotation save failed, warned or produced no bytes')
                result['derivative_sha256'] = digest(target)
                result['derivative_path'] = str(target)
                private_path = directory / 'SavedState.private.json'
                write_json(private_path, {'edge_persist_id': list(token)})
                result['private_state_path'] = str(private_path)
                result['private_state_sha256'] = digest(private_path)
            result['passed'] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    rec.call('close owned drawing', controller.close_doc, author.model)
                    author.model = None
                except Exception as error:
                    rec.failure(error, cleanup=True)
            if controller is not None:
                try:
                    rec.call('gracefully close owned oracle', controller.close)
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result['controller_diagnostics'] = controller.diagnostics
    result['dialogs'] = dialogs.log
    result['progress_windows'] = dialogs.progress
    result['input_sha256_after'] = digest(source)
    result['passed'] = bool(result['passed'] and rec.data['first_failure'] is None and not rec.data['cleanup_errors']
                            and not dialogs.log and not result.get('controller_diagnostics') and result['input_sha256_after'] == source_sha)
    rec.data['passed'] = result['passed']
    rec.data['measurement'] = result
    rec.flush()
    write_json(directory / 'Result.json', result)
    return result


def dispatch(packet, packet_sha, output, role, case, *, source, source_sha, prior=None, tree=None):
    directory = output / role
    job = {'packet': str(packet), 'packet_sha256': packet_sha, 'case': case, 'directory': str(directory),
           'source': str(source), 'source_sha256': source_sha, 'prior': prior, 'tree': tree}
    job_path = output / (role + '.job.json')
    write_json(job_path, job)
    try:
        process = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), 'worker', str(job_path)], capture_output=True, text=True, timeout=240, check=False)
        captured = {'exit_code': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr, 'timed_out': False}
    except subprocess.TimeoutExpired as error:
        captured = {'exit_code': None, 'stdout': str(error.stdout or ''), 'stderr': str(error.stderr or ''), 'timed_out': True}
    write_json(output / (role + '.transport.json'), captured)
    result = json.loads((directory / 'Result.json').read_bytes()) if (directory / 'Result.json').is_file() else {'passed': False}
    result['worker_exit_code'] = captured['exit_code']
    result['worker_timed_out'] = captured['timed_out']
    result['passed'] = bool(result['passed'] and captured['exit_code'] == 0 and not captured['timed_out'])
    return result


def stage_generated(root, case):
    if case.get('drawing_target') is None:
        return root / case['drawing_source']
    for label in ('part', 'drawing'):
        source = root / case[label + '_source']
        target = Path(case[label + '_target'])
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            require(digest(target) == case[label + '_sha256'], 'existing encoded guest slot differs; overwrite refused')
        else:
            with target.open('xb') as output:
                output.write(source.read_bytes())
        require(digest(target) == case[label + '_sha256'], 'encoded guest slot changed')
    return Path(case['drawing_target'])


def run(packet, packet_sha):
    require(os.name == 'nt', 'only the root-owned Windows oracle may execute this protocol')
    request = verify(packet, packet_sha)
    root = packet.parent
    output = root / 'Inspection'
    output.mkdir()
    result = {'schema': SCHEMA, 'passed': False, 'native_acceptance': False, 'heldout_inputs_read': 0,
              'packet_sha256': packet_sha, 'phases': {}, 'started_at': time.time()}
    control, generated = request['cases']
    control_path = root / control['drawing_source']
    phases = result['phases']

    def checkpoint():
        write_json(output / 'Result.json', result)

    def lane(name, case, source, source_sha, tree=None):
        first = dispatch(packet, packet_sha, output, name + 'OpenEditSave', case, source=source, source_sha=source_sha, tree=tree)
        phases[name + 'OpenEditSave'] = first
        checkpoint()
        if not first['passed']:
            return False, first
        reopened = dispatch(packet, packet_sha, output, name + 'FreshReopen', case, source=Path(first['derivative_path']), source_sha=first['derivative_sha256'], prior=first)
        phases[name + 'FreshReopen'] = reopened
        checkpoint()
        return reopened['passed'], first

    before = None
    try:
        before_passed, before = lane('ControlBefore', control, control_path, control['drawing_sha256'])
        result['control_before_passed'] = before_passed
        if before_passed:
            generated_path = stage_generated(root, generated)
            candidate_passed, candidate = lane('Generated', generated, generated_path, generated['drawing_sha256'], generated.get('drawing_tree'))
            result['generated_passed'] = candidate_passed
        else:
            result['generated_skipped'] = 'the exact native control did not prove the edge annotation lifecycle'
    except Exception as error:
        result['error'] = repr(error)
    finally:
        try:
            tail_tree = before['initial_state']['drawing_tree'] if before and before.get('initial_state') else None
            after_passed, _ = lane('ControlAfter', control, control_path, control['drawing_sha256'], tail_tree)
            result['control_after_passed'] = after_passed
        except Exception as error:
            result['control_after_passed'] = False
            result['control_after_error'] = repr(error)
        try:
            verify(packet, packet_sha)
            result['inputs_unchanged'] = all(digest(root / case[label + '_source']) == case[label + '_sha256'] for case in request['cases'] for label in ('drawing', 'part'))
            result['encoded_slots_unchanged'] = all(digest(Path(generated[label + '_target'])) == generated[label + '_sha256'] for label in ('drawing', 'part')) if generated.get('drawing_target') else True
        except Exception as error:
            result['inputs_unchanged'] = False
            result['custody_error'] = repr(error)
        identities = [p.get('oracle_identity', {}).get('process_creation_filetime') for p in phases.values()]
        result['distinct_processes'] = len(set(identities) - {None})
        result['controls_healthy'] = result.get('control_before_passed') is True and result.get('control_after_passed') is True
        result['passed'] = bool(result['controls_healthy'] and result.get('generated_passed') and result.get('inputs_unchanged')
                                and result.get('encoded_slots_unchanged') and len(phases) == result['distinct_processes'] == 6
                                and all(p['passed'] for p in phases.values()))
        result['cache_consumer_measured'] = False
        result['finished_at'] = time.time()
        checkpoint()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('verify', 'run', 'worker'))
    parser.add_argument('path', type=Path)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.command == 'worker':
        require(os.name == 'nt', 'worker requires the root-owned Windows guest')
        job = json.loads(args.path.read_bytes())
        result = phase(Path(job['packet']), job['packet_sha256'], job['case'], Path(job['directory']), Path(job['source']), job['source_sha256'], prior=job['prior'], expected_tree=job['tree'])
        return 0 if result['passed'] else 3
    require(args.sha256 is not None, 'the exact frozen packet hash is required')
    packet = args.path.resolve(strict=True)
    if args.command == 'verify':
        verify(packet, args.sha256)
        print(json.dumps({'passed': True, 'native_processes_started': 0, 'native_acceptance': False}))
        return 0
    result = run(packet, args.sha256)
    print(json.dumps({key: result[key] for key in ('passed', 'controls_healthy', 'distinct_processes', 'cache_consumer_measured')}))
    return 0 if result['passed'] else 3


if __name__ == '__main__':
    raise SystemExit(main())
