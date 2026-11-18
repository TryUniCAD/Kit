from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PureWindowsPath
import sys

from AuthorCurves import digest, require, write_json
from InspectCombinedPlanarMates import ORACLE, phase, signature
from InspectSdkPlanarGroup import observe_options, TOOLS as GROUP_TOOLS
from PortableAsmPrediction import predict
from SdkPlanarGroupPrediction import state_matches

SCHEMA = 'kit.sw2026.portable-assembly-disclosed-trial.v1'
TOOLS = (*GROUP_TOOLS, 'PortableAsmPrediction.py', Path(__file__).name)
CONTROL_PARENT = 'fac5708432e569e787dfc00aa87fe08e5ef2d6830ec88f2d69525f8030d9fd1f'
CONTROL_CHILD = 'b46e1e0f066db55730ce765cb2547b97ad1416e1ea0ceaa588bb8e819f727321'


def checked(path, wanted):
    require(path.is_file() and not path.is_symlink() and digest(path) == wanted, 'frozen portable assembly input changed: ' + path.name)
    return path


def locator(row):
    return Path(row['windows_path'] if os.name == 'nt' else row['host_path'])


def verify(path, sha):
    root = path.parent
    job = json.loads(checked(path, sha).read_bytes())
    require(job['schema'] == SCHEMA and job['oracle_sha256'] == ORACLE and job['native_acceptance'] is False and job['heldout_inputs_read'] == 0, 'expected the disclosed unqualified portable assembly trial')
    require(Path(__file__).resolve().parent == (root / 'Tools').resolve(strict=True) and set(job['tools_sha256']) == set(TOOLS), 'use the exact frozen portable assembly observer tools')
    for name, wanted in job['tools_sha256'].items():
        checked(root / 'Tools' / name, wanted)
    fixture = json.loads(checked(root / 'Fixture.json', job['fixture_sha256']).read_bytes())
    request = json.loads(checked(root / 'NeutralRequest.json', fixture['request_sha256']).read_bytes())
    expected = json.loads(checked(root / 'Prediction.json', fixture['prediction_sha256']).read_bytes())
    require(predict(request) == expected and expected['writer_frames_or_readback_used'] is False, 'independent portable prediction changed')
    producer = json.loads(checked(root / 'ProducerResult.json', fixture['producer_sha256']).read_bytes())
    require(producer['passed'] and producer['registration_scope'] == 'private writer registry only' and producer['application_usable'] is False and producer['vendor_loadable'] is False, 'producer changed its scope or invented native acceptance')
    require(producer['native_processes_started'] == 0 and fixture['source_manifest_sha256'] == job['source_manifest_sha256'], 'producer changed source custody')
    checked(root / 'SourceManifest.json', job['source_manifest_sha256'])
    paths = {}
    for key, row in fixture['files'].items():
        source = checked(root / 'FrozenGenerated' / row['file'], row['sha256'])
        native = PureWindowsPath(row['encoded_path'])
        require(native.is_absolute() and native.name == row['file'] and source.stat().st_size == row['bytes'] and producer['files'][key]['sha256'] == row['sha256'], 'portable artifact differs from normal registry output')
        paths[key] = source, Path(native), row['sha256']
    control = json.loads(checked(root / 'ControlCase.json', job['control_case_sha256']).read_bytes())
    require(control['case']['name'] == 'A22CombinedRotated' and control['child_size_m'] == [.04, .02, .01], 'only the disclosed named control is admitted')
    controls = tuple(checked(locator(job['control'][key]), wanted) for key, wanted in (('parent', CONTROL_PARENT), ('child', CONTROL_CHILD)))
    require(all(str(paths[key][1]).casefold() != str(controls[index]).casefold() for index, key in enumerate(('assembly', 'child'))), 'generated output cannot overwrite a control')
    return fixture, expected, paths, control, controls


def run(path, sha):
    require(os.name == 'nt', 'only root may execute the serial pinned windows oracle')
    fixture, expected, paths, control, controls = verify(path, sha)
    output = path.parent / 'Inspection'
    output.mkdir()
    rows = {}
    report = {'schema': SCHEMA, 'packet_sha256': sha, 'source_manifest_sha256': fixture['source_manifest_sha256'], 'phases': rows, 'native_acceptance': False, 'heldout_inputs_read': 0, 'passed': False}
    job = {'case': expected['case'], 'child_size_m': [expected['child_dimensions_m'][key] for key in ('width', 'height', 'depth')], 'edit_distance_m': expected['edit_distance_m']}
    control_expected = {'case': control['case'], 'assembly_configuration': 'Default', 'child_configuration': 'Default',
        'child_parameters_m': {'D1@Sketch1': .04, 'D2@Sketch1': .02, 'D1@Boss-Extrude1': .01},
        'occurrence_names': ['CohortChild-' + str(index + 1) for index in range(len(control['case']['placements']))]}
    def record(role, selected, edit, chosen, **options):
        rows[role] = phase(selected, edit, role, *chosen, output / role, **options)
        write_json(output / 'Result.json', report)
        return rows[role]
    try:
        before = record('ControlBefore', control, control['case'], controls, observe=lambda author, model, child: observe_options(author, model, child, control_expected))
        if before['passed']:
            require(all(not native.exists() and not native.is_symlink() for _, native, _ in paths.values()), 'working native paths must both be unused before copying')
            for source, native, wanted in paths.values():
                native.parent.mkdir(exist_ok=True)
                with source.open('rb') as incoming, native.open('xb') as target:
                    target.write(incoming.read())
                require(digest(native) == wanted, 'new working copy differs from its frozen generated bytes')
            targets = tuple(paths[key][1] for key in ('assembly', 'child'))
            observe = lambda author, model, child: observe_options(author, model, child, expected)
            first = record('Generated', job, expected['edited_case'], targets, editing=True, observe=observe)
            if first['passed']:
                reopened = record('FreshReopen', job, expected['edited_case'], targets, reopened=first['saved'], observe=observe)
                report['exact_prediction'] = all(state_matches(first[key], expected['initial'], expected) for key in ('initial', 'rebuilt')) and state_matches(first['edited'], expected['edited'], expected) and all(state_matches(reopened[key], expected['edited'], expected) for key in ('initial', 'rebuilt'))
                report['edit_identity_preserved'] = signature(first['rebuilt']) == signature(first['edited'])
                report['reopen_identity_preserved'] = signature(first['edited']) == signature(reopened['rebuilt'])
    except Exception as error:
        report['error'] = repr(error)
    finally:
        after = record('ControlAfter', control, control['case'], controls, observe=lambda author, model, child: observe_options(author, model, child, control_expected))
        verify(path, sha)
        report['controls_healthy'] = bool(rows.get('ControlBefore', {}).get('passed') and after['passed'])
        identities = [value['oracle_identity']['process_creation_filetime'] for value in rows.values() if value.get('oracle_identity')]
        report['distinct_processes'] = len(identities) == len(set(identities)) == len(rows) == 4
        report['input_immutability'] = all(digest(source) == wanted for source, _, wanted in paths.values())
        report['passed'] = bool(report['controls_healthy'] and report['distinct_processes'] and report['input_immutability'] and all(value.get('passed') for value in rows.values()) and all(report.get(key) for key in ('exact_prediction', 'edit_identity_preserved', 'reopen_identity_preserved')))
        report['native_acceptance'] = report['passed']
        write_json(output / 'Result.json', report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('verify', 'run'))
    parser.add_argument('packet', type=Path)
    parser.add_argument('--packet-sha256', required=True)
    args = parser.parse_args()
    if args.mode == 'verify':
        fixture, expected, *_ = verify(args.packet.resolve(strict=True), args.packet_sha256)
        print(json.dumps({'passed': True, 'native_processes_started': 0, 'tree_rows': {key: len(value) for key, value in expected['tree'].items()}, 'occurrences': expected['initial']['body_count'], 'native_acceptance': False}, sort_keys=True))
    else:
        result = run(args.packet.resolve(strict=True), args.packet_sha256)
        print(json.dumps({'passed': result['passed'], 'result': str(args.packet.parent / 'Inspection/Result.json')}, sort_keys=True))
        raise SystemExit(0 if result['passed'] else 3)


if __name__ == '__main__':
    main()
