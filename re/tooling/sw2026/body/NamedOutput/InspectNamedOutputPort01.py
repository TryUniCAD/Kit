from argparse import ArgumentParser
from json import dumps, loads
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfile

import AuthorCurves as curves
from AuthorRectangleAnchors import CONTROL, ORACLE, control
import InspectSdkBlindPart as part
from PredictNamedOutput01 import prediction as predict


SCHEMA = 'kit.sw2026.sdk-named-output-native-discovery.v1'
TOOLS = {'InspectNamedOutputPort01.py', 'AuthorCurves.py', 'AuthorRectangleAnchors.py',
         'InspectFresh.py', 'InspectSdkBlindPart.py', 'OracleIdentity.py', 'Swapp.py',
         'PredictNamedOutput01.py'}
BASE_SNAPSHOT = part.snapshot
BASE_VERIFY = part.verify_state


def snapshot(author, case):
    value = BASE_SNAPSHOT(author, case)
    bodies = tuple(author.get(author.typed(author.model, 'PartDoc'), 'GetBodies2', 0, False) or ())
    curves.require(len(bodies) == 1, 'named output requires exactly one actual solid body')
    body, = bodies
    value.update(native_body_name=str(author.get(body, 'Name')),
        native_body_type=int(author.get(body, 'GetType')), complete_solid_count=len(bodies),
        topology={name:int(author.get(body, method)) for name,method in
            (('faces','GetFaceCount'),('edges','GetEdgeCount'),('vertices','GetVertexCount'))})
    rows = []
    for expected in case['intent']['drivers']:
        handle = author.get(author.model, 'Parameter', expected['reference'])
        curves.require(handle is not None, 'actual named dimension was not found: '+expected['reference'])
        rows.append({'role':expected['role'], 'reference':expected['reference'],
            'name':str(author.get(handle, 'Name')), 'full_name':str(author.get(handle, 'FullName')),
            'value_m':float(author.get(handle, 'SystemValue')),
            'driving':int(author.get(handle, 'DrivenState')) == 2 and not bool(author.get(handle, 'ReadOnly'))})
    value['actual_drivers'] = rows
    return value


def verify_state(recorder, value, case, expected_tree, *, edited):
    intent = case['intent']
    target = case['edit']['expected'] if edited else case['expected_initial']
    expected_depth = case['edit']['new_depth_m'] if edited else intent['depth_m']
    observed = [[row['name'],row['type'],row['parent']] for row in value['tree']]
    curves.require(observed == expected_tree and not any(row['suppressed'] or row['error'] or row['warning'] for row in value['tree']),
        'complete ordered native feature tree or diagnostic state differs')
    curves.require(value['configuration'] == intent['configuration_name']
        and value['sketch_parents'] == [intent['support']]
        and value['boss_parents'] == [intent['profile'],intent['support']],
        'actual configuration or profile and boss ownership differs')
    curves.require(value['dimension_driving'] and value['sketch_relation_count'] == intent['relation_count']
        and value['sketch_has_display_dimensions'] == intent['has_sketch_display_dimensions'],
        'actual driving dimensions display or solver relation inventory differs')
    curves.require(value['whats_wrong'] == 0 and value['body_count'] == value['complete_solid_count'] == target['body_count']
        and value['native_body_type'] == 0 and value['native_body_name'] == case['body_label']
        and value['topology'] == {'faces':6,'edges':12,'vertices':8},
        'actual body label type inventory topology or diagnostics differ')
    recorder.close_number('actual named depth', value['dimension_m'], expected_depth)
    for key, intended in (('volume','volume_m3'),('area','area_m2'),('mass','mass_kg')):
        recorder.close_number('analytic named '+key, value['mass'][key], target[intended], absolute=1e-16)
    for actual, expected in zip(value['mass']['com'],target['centre_of_mass_m'],strict=True):
        recorder.close_number('analytic named centre of mass',actual,expected)
    curves.require(len(value['actual_drivers']) == len(intent['drivers']), 'actual named driver count differs')
    for actual, expected in zip(value['actual_drivers'],intent['drivers'],strict=True):
        full_name = actual['full_name'].split('@')
        curves.require(actual['role'] == expected['role'] and actual['reference'] == expected['reference']
            and actual['name'] == expected['name'] and actual['driving']
            and len(full_name) >= 3 and full_name[:2] == [expected['name'],expected['owner']],
            'actual named driver does not retain its exact native owner')
        target_value = expected_depth if expected['role'] == 'depth' else expected['value_m']
        recorder.close_number('actual '+expected['role']+' driver',actual['value_m'],target_value)
    points = intent['vertices_m']
    expected_edges = sorted(tuple(sorted((tuple(first),tuple(last)))) for first,last in zip(points,points[1:]+points[:1],strict=True))
    geometry = value['sketch_geometry']
    curves.require(len(geometry) == 4 and all(row['kind'] == 'line' and not row['construction'] for row in geometry),
        'the complete native sketch is not the authored four line contour')
    observed_edges = sorted(tuple(sorted((tuple(row['start']),tuple(row['end'])))) for row in geometry)
    for actual, expected in zip(observed_edges,expected_edges,strict=True):
        for actual_point, expected_point in zip(actual,expected,strict=True):
            for coordinate, target_coordinate in zip(actual_point,expected_point,strict=True):
                recorder.close_number('authored local rectangle coordinate',coordinate,target_coordinate)


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    curves.require(curves.digest(packet) == expected, 'typed named native trial changed')
    job = loads(packet.read_bytes())
    curves.require(job['schema'] == SCHEMA and job['oracle_sha256'] == ORACLE
        and job['control_sha256'] == CONTROL and job['heldout_inputs_read'] == 0
        and job['public_writer_enabled'] is False and job['original_source_qualification'] is False,
        'typed named trial source or scope claim differs')
    tools = root/'Tools'
    curves.require(Path(__file__).resolve().parent == tools and set(job['tools_sha256']) == TOOLS,
        'typed named trial requires the exact complete observer set')
    for name, checksum in job['tools_sha256'].items():
        curves.require(curves.digest(tools/name) == checksum, 'typed named native tool changed: '+name)
    for name, checksum in job['inputs_sha256'].items():
        path = (root/name).resolve(strict=True)
        curves.require(path.is_relative_to(root) and path.is_file() and curves.digest(path) == checksum,
            'typed named native input changed: '+name)
    proof = loads((root/'ProcessProof.json').read_bytes())
    curves.require(proof['passed'] and proof['process_count'] == 44 and proof['source_unchanged']
        and proof['heldout_inputs_read'] == 0 and not proof['public_writer_registration_changed'],
        'typed named trial lacks the frozen guarded source-only qualification')
    for case in job['cases']:
        build = loads((root/case['named_build']).read_bytes())
        repeat = loads((root/case['repeat_build']).read_bytes())
        default = loads((root/case['plain_build']).read_bytes())
        curves.require(build == repeat and build['passed'] and default['passed']
            and build['artifact_sha256'] == job['inputs_sha256'][case['named_file']]
            and default['artifact_sha256'] == job['inputs_sha256'][case['plain_file']]
            and build['plain_artifact_sha256'] == default['artifact_sha256']
            and build['typed_roundtrip_exact'] and build['cross_stream_alias_exact']
            and build['logical_stream_difference'] == ['Contents/Config-0','Contents/Config-0-ResolvedFeatures']
            and len(build['streams']) == len(default['streams']) == 10
            and not build['runtime_access_attempts'] and not default['runtime_access_attempts']
            and build['source_document_unchanged'] and default['source_document_unchanged']
            and not build['unexpected_sdk_origins'] and not build['research_runtime_imports']
            and build['writer_registration_gate']['supports'] is False
            and build['writer_registration_gate']['output_bytes'] == 0,
            'typed named case is not the declared source-only owner construction')
        prediction = case['prediction']
        curves.require(prediction == predict(build), 'native comparison method differs from its exact neutral model')
        spec = build['spec']
        curves.require(prediction['body_label'] == spec['body_label']
            and prediction['intent']['self_path'] == spec['self_path']
            and prediction['intent']['model_name'] == spec['model_name']
            and prediction['intent']['width_mm'] == spec['width_mm']
            and prediction['intent']['height_mm'] == spec['height_mm']
            and prediction['intent']['depth_m'] == spec['depth_mm']*0.001
            and prediction['edit']['new_depth_m'] == spec['edited_depth_mm']*0.001,
            'typed named native prediction differs from its original neutral spec')
        path = PureWindowsPath(prediction['intent']['self_path'])
        curves.require(path.parent == PureWindowsPath(r'C:\KitSdkCandidates')
            and path.name == prediction['intent']['model_name']+'.SLDPRT'
            and path.stem.startswith('SdkNamePort'), 'typed named native path is outside its owned slots')
        part.tree_prediction(case['tree_request'],prediction)
    curves.require(len(job['cases']) == 5 and job['expected_native_processes'] == 17,
        'typed named native trial cohort differs')
    return job


def stage(source, target, expected, replace_hash=None):
    curves.require(curves.digest(source) == expected, 'typed named staging source changed')
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        actual = curves.digest(target)
        if actual == expected:
            return
        curves.require(replace_hash is not None and actual == replace_hash,
            'typed named staging slot has unrelated existing bytes')
    copyfile(source,target)
    curves.require(curves.digest(target) == expected, 'typed named staged bytes differ')


def run(packet, expected):
    curves.require(os.name == 'nt', 'only root runs the pinned oracle in the reserved Windows guest')
    job = verify(packet,expected)
    root = packet.parent
    output = root/'Inspection'
    output.mkdir()
    phases = {}
    report = {'schema':SCHEMA,'packet_sha256':expected,'phases':phases,'passed':False,
        'heldout_inputs_read':0,'public_writer_enabled':False,'original_source_qualification':False}
    part.snapshot, part.verify_state = snapshot, verify_state

    def checkpoint():
        curves.write_json(output/'Result.json',report)

    try:
        phases['ControlBefore'] = control(output,'ControlBefore',root/'Control.SLDPRT')
        checkpoint()
        if phases['ControlBefore']['passed']:
            for case in job['cases']:
                name = case['name']
                prediction = case['prediction']
                path = Path(prediction['intent']['self_path'])
                tree = part.tree_prediction(case['tree_request'],prediction)
                plain_hash = job['inputs_sha256'][case['plain_file']]
                named_hash = job['inputs_sha256'][case['named_file']]
                stage(root/case['plain_file'],path,plain_hash,replace_hash=named_hash)
                plain_case = {**prediction,'body_label':prediction['intent']['feature']}
                phases[name+'Plain'] = part.phase(output,name+'Plain',path,plain_hash,plain_case,tree,measure_only=True)
                checkpoint()
                if not phases[name+'Plain']['passed']:
                    continue
                stage(root/case['named_file'],path,named_hash,replace_hash=plain_hash)
                phases[name+'Named'] = part.phase(output,name+'Named',path,named_hash,prediction,tree)
                checkpoint()
                trial = phases[name+'Named']
                if trial['passed']:
                    phases[name+'Reopen'] = part.phase(output,name+'Reopen',output/(name+'Named')/'Edited.SLDPRT',
                        trial['derivative_sha256'],prediction,tree,edited_tree=trial['states']['Edited']['tree'])
                checkpoint()
    except Exception as error:
        report['error'] = repr(error)
    finally:
        phases['ControlAfter'] = control(output,'ControlAfter',root/'Control.SLDPRT')
        verify(packet,expected)
        births = {value.get('oracle_identity',{}).get('process_creation_filetime')
                  for value in phases.values() if value.get('oracle_identity')}
        report.update(controls_healthy=phases['ControlBefore']['passed'] and phases['ControlAfter']['passed'],
            distinct_processes=len(births-{None}),frozen_inputs_unchanged=True)
        report['passed'] = len(phases) == report['distinct_processes'] == job['expected_native_processes'] and all(value['passed'] for value in phases.values())
        checkpoint()
        part.snapshot, part.verify_state = BASE_SNAPSHOT, BASE_VERIFY
    return report


def main():
    parser = ArgumentParser()
    parser.add_argument('command',choices=('verify','run'))
    parser.add_argument('packet',type=Path)
    parser.add_argument('--packet-sha256',required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == 'verify':
        verify(packet,args.packet_sha256)
        value = {'passed':True,'processes_started':0}
    else:
        report = run(packet,args.packet_sha256)
        value = {name:report[name] for name in ('passed','controls_healthy','distinct_processes')}
    print(dumps(value,sort_keys=True))
    raise SystemExit(0 if value['passed'] else 3)


if __name__ == '__main__':
    main()
