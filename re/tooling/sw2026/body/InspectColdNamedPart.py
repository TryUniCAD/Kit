from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfile

import AuthorCurves as curves
from AuthorRectangleAnchors import CONTROL, ORACLE, control
import InspectSdkBlindPart as part


SCHEMA = 'kit.sw2026.cold-named-body-native-discovery.v1'
TOOLS = {'InspectColdNamedPart.py', 'AuthorCurves.py', 'AuthorRectangleAnchors.py',
         'InspectFresh.py', 'InspectSdkBlindPart.py', 'OracleIdentity.py', 'Swapp.py'}
BASE_SNAPSHOT = part.snapshot
BASE_VERIFY = part.verify_state


def snapshot(author, case):
    value = BASE_SNAPSHOT(author, case)
    bodies = tuple(author.get(author.typed(author.model, 'PartDoc'), 'GetBodies2', 0, False) or ())
    curves.require(len(bodies) == 1, 'cold name experiment requires the actual sole solid body')
    body, = bodies
    value.update(native_body_name=str(author.get(body, 'Name')),
                 native_body_type=int(author.get(body, 'GetType')),
                 complete_solid_count=len(bodies),
                 topology={name: int(author.get(body, method)) for name, method in
                    (('faces', 'GetFaceCount'), ('edges', 'GetEdgeCount'), ('vertices', 'GetVertexCount'))})
    return value


def verify_state(recorder, value, case, expected_tree, *, edited):
    intent = case['intent']
    vertices = intent['vertices_m']
    curves.require(all(len(point) == 3 and point[2] == 0.0 for point in vertices),
                   'the neutral corner prediction must be on its exact local XY plane')
    planar_case = {**case, 'intent': {**intent, 'vertices_m': [point[:2] for point in vertices]}}
    BASE_VERIFY(recorder, value, planar_case, expected_tree, edited=edited)
    target = case['edit']['expected'] if edited else case['expected_initial']
    recorder.close_number('cold analytic solid mass', value['mass']['mass'],
                          target['mass_kg'], absolute=1e-12)
    curves.require(value['native_body_name'] == case['body_label']
        and value['native_body_type'] == 0 and value['complete_solid_count'] == 1
        and value['topology'] == {'faces': 6, 'edges': 12, 'vertices': 8},
        'cold atom name or complete analytic body topology differs from the neutral input')


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    curves.require(curves.digest(packet) == expected, 'cold native trial changed')
    job = loads(packet.read_bytes())
    curves.require(job['schema'] == SCHEMA and job['oracle_sha256'] == ORACLE
        and job['control_sha256'] == CONTROL and job['heldout_inputs_read'] == 0
        and job['named_body_writer_qualified'] is False, 'cold native trial has an unqualified source claim')
    tools = root / 'Tools'
    curves.require(Path(__file__).resolve().parent == tools and set(job['tools_sha256']) == TOOLS,
                   'cold native trial needs the exact complete observer set')
    for name, expected_hash in job['tools_sha256'].items():
        curves.require(curves.digest(tools / name) == expected_hash, 'cold native observer changed: ' + name)
    for name, expected_hash in job['inputs_sha256'].items():
        value = (root / name).resolve(strict=True)
        curves.require(value.is_relative_to(root) and value.is_file() and curves.digest(value) == expected_hash,
                       'cold native input custody differs: ' + name)
    curves.require(job['inputs_sha256']['Control.SLDPRT'] == CONTROL, 'cold native pristine source changed')
    proof = loads((root / 'BuildProof.json').read_bytes())
    curves.require(proof['passed'] and proof['process_count'] == 6 and proof['heldout_inputs_read'] == 0,
                   'cold native trial requires two complete independent guarded design builds')
    for case in job['cases']:
        build = loads((root / case['named_build']).read_bytes())
        repeat = loads((root / case['repeat_build']).read_bytes())
        plain = loads((root / case['plain_build']).read_bytes())
        curves.require(build == repeat and build['passed'] and plain['passed']
            and build['runtime_input_file_reads'] == plain['runtime_input_file_reads'] == 0
            and build['typed_roundtrip_exact'] and build['cross_stream_alias_exact']
            and build['plain_artifact_sha256'] == plain['artifact_sha256']
            and build['artifact_sha256'] == job['inputs_sha256'][case['named_file']]
            and plain['artifact_sha256'] == job['inputs_sha256'][case['plain_file']]
            and build['logical_stream_difference'] == ['Contents/Config-0', 'Contents/Config-0-ResolvedFeatures']
            and not any('Partition' in name for name in build['streams'])
            and build['heldout_inputs_read'] == plain['heldout_inputs_read'] == 0,
            'cold name candidate is not the declared deterministic no-cache owner experiment')
        prediction = case['prediction']
        curves.require(prediction == build['prediction'] and case['tree_request'] == build['tree_request'],
                       'cold native comparison was not derived from its exact neutral request')
        path = PureWindowsPath(prediction['intent']['self_path'])
        curves.require(path.parent == PureWindowsPath(r'C:\KitSdkCandidates')
            and path.name == prediction['intent']['model_name'] + '.SLDPRT'
            and 'ColdName' in path.stem, 'cold native path is outside its owned experiment slot')
        part.tree_prediction(case['tree_request'], prediction)
    return job


def stage(source, target, expected, replace_hash=None):
    curves.require(curves.digest(source) == expected, 'cold staging source changed')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = curves.digest(target)
        if existing == expected:
            return
        curves.require(replace_hash is not None and existing == replace_hash,
                       'cold staging path has unrelated preexisting bytes')
    copyfile(source, target)
    curves.require(curves.digest(target) == expected, 'cold staged bytes differ')


def run(packet, expected):
    curves.require(os.name == 'nt', 'only root may execute the native trial in the reserved Windows guest')
    job = verify(packet, expected)
    root = packet.parent
    output = root / 'Inspection'
    output.mkdir()
    phases = {}
    report = {'schema': SCHEMA, 'packet_sha256': expected, 'phases': phases,
        'passed': False, 'heldout_inputs_read': 0, 'named_body_writer_qualified': False}
    part.snapshot, part.verify_state = snapshot, verify_state

    def checkpoint():
        curves.write_json(output / 'Result.json', report)

    try:
        phases['ControlBefore'] = control(output, 'ControlBefore', root / 'Control.SLDPRT')
        checkpoint()
        if phases['ControlBefore']['passed']:
            for case in job['cases']:
                name = case['name']
                prediction = case['prediction']
                path = Path(prediction['intent']['self_path'])
                tree = part.tree_prediction(case['tree_request'], prediction)
                plain_hash = job['inputs_sha256'][case['plain_file']]
                named_hash = job['inputs_sha256'][case['named_file']]
                stage(root / case['plain_file'], path, plain_hash)
                plain_case = {**prediction, 'body_label': prediction['intent']['feature']}
                phases[name + 'Plain'] = part.phase(output, name + 'Plain', path,
                    plain_hash, plain_case, tree, measure_only=True)
                checkpoint()
                if not phases[name + 'Plain']['passed']:
                    continue
                stage(root / case['named_file'], path, named_hash, replace_hash=plain_hash)
                phases[name + 'Named'] = part.phase(output, name + 'Named', path,
                    named_hash, prediction, tree)
                checkpoint()
                trial = phases[name + 'Named']
                if trial['passed']:
                    phases[name + 'Reopen'] = part.phase(output, name + 'Reopen',
                        output / (name + 'Named') / 'Edited.SLDPRT', trial['derivative_sha256'],
                        prediction, tree, edited_tree=trial['states']['Edited']['tree'])
                checkpoint()
    except Exception as error:
        report['error'] = repr(error)
    finally:
        phases['ControlAfter'] = control(output, 'ControlAfter', root / 'Control.SLDPRT')
        verify(packet, expected)
        births = {value.get('oracle_identity', {}).get('process_creation_filetime')
                  for value in phases.values() if value.get('oracle_identity')}
        report.update(controls_healthy=phases['ControlBefore']['passed'] and phases['ControlAfter']['passed'],
                      distinct_processes=len(births - {None}), frozen_inputs_unchanged=True)
        report['passed'] = len(phases) == report['distinct_processes'] == 8 and all(row['passed'] for row in phases.values())
        checkpoint()
        part.snapshot, part.verify_state = BASE_SNAPSHOT, BASE_VERIFY
    return report


def main():
    parser = ArgumentParser()
    parser.add_argument('command', choices=('verify', 'run'))
    parser.add_argument('packet', type=Path)
    parser.add_argument('--packet-sha256', required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == 'verify':
        verify(packet, args.packet_sha256)
        result = {'passed': True, 'processes_started': 0}
    else:
        report = run(packet, args.packet_sha256)
        result = {name: report[name] for name in ('passed', 'controls_healthy', 'distinct_processes')}
    print(dumps(result, sort_keys=True))
    raise SystemExit(0 if result['passed'] else 3)


if __name__ == '__main__':
    main()
