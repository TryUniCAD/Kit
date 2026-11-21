from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
import os
from pathlib import Path

import AuthorCurves as curves
from AuthorRectangleAnchors import CONTROL, ORACLE
from AuthorPartDriverNames import find_body, measure, save, compare
from InspectSdkCornerOwners import control_match, control_phase


SCHEMA = 'kit.sw2026.unicode-body-name-source.v1'
TOOLS = {'AuthorUnicodeBodyNames.py', 'AuthorPartDriverNames.py', 'AuthorCurves.py',
    'AuthorRectangleAnchors.py', 'InspectFresh.py', 'InspectSdkBlindPart.py',
    'InspectSdkCornerOwners.py', 'InspectCornerPointOwners.py', 'SdkCornerOwnerGraph.py',
    'OracleIdentity.py', 'Swapp.py'}


def checked(root, name, expected):
    path = (root / name).resolve(strict=True)
    curves.require(path.parent == root and path.is_file() and curves.digest(path) == expected,
                   'unicode disclosed source or tool differs: ' + name)
    return path


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    job = loads(checked(root, packet.name, expected).read_bytes())
    curves.require(job['schema'] == SCHEMA and job['oracle_sha256'] == ORACLE
        and job['control_sha256'] == CONTROL and job['heldout_inputs_read'] == 0
        and job['writer_output_count'] == 0, 'unicode source job is not the disclosed reader-only profile')
    tools = root / 'Tools'
    curves.require(Path(__file__).resolve().parent == tools and set(job['tools_sha256']) == TOOLS,
                   'unicode source job requires the exact complete observer')
    for name, checksum in job['tools_sha256'].items():
        checked(tools, name, checksum)
    checked(root, 'Control.SLDPRT', CONTROL)
    curves.require(tuple(case['name'] for case in job['cases']) == ('Accent', 'Bmp', 'Supplementary'),
                   'unicode source job requires all three independent lexical probes')
    for case in job['cases']:
        checked(root, case['source'], case['source_sha256'])
        encoded = case['body_name'].encode('utf-16-le')
        units = [int.from_bytes(encoded[index:index + 2], 'little') for index in range(0, len(encoded), 2)]
        curves.require(case['expected_utf16_units'] == units and case['body_name'] != 'AnchorBoss'
            and len(case['drivers']) == 3 and len(case['body_name']) < 100
            and all(row['original_name'] == row['new_name'] and row['original_name'] in ('D1', 'D2') for row in case['drivers']),
            'unicode source must vary body text alone with explicit valid UTF-16')
    return job


def expected_geometry(author, observed, case):
    expected = case['expected_source_dimensions_m']
    for key, value in zip(observed['drivers_m'], expected, strict=True):
        author.rec.close_number('unchanged disclosed source driver', observed['drivers_m'][key], value)
    width, height, depth = expected
    author.rec.close_number('disclosed source prism volume', observed['mass']['volume'],
                            width * height * depth, absolute=1e-16)
    author.rec.close_number('disclosed source prism area', observed['mass']['area'],
                            2 * (width * height + (width + height) * depth), absolute=1e-16)


def phase(folder, source, checksum, case, previous=None):
    import Swapp
    from OracleIdentity import application_identity

    folder.mkdir(parents=True, exist_ok=False)
    rec = curves.Recorder(folder / 'Record.json', {'case': case['name'],
        'role': 'Author' if previous is None else 'Fresh', 'source_sha256': checksum})
    result = {'passed': False, 'expected_utf16_units': case['expected_utf16_units']}
    rec.data['result'] = result
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            curves.require(curves.digest(source) == checksum, 'unicode source changed before opening')
            rec.call('guard idle owned unicode oracle', Swapp.sweep)
            controller = rec.call('start fresh owned unicode oracle', Swapp.Sw)
            identity = rec.call('bind exact unicode oracle', application_identity, controller.app)
            result['oracle_identity'] = identity
            curves.require(identity['version_matches'] and identity['sha256'] == ORACLE
                           and controller.revision == '34.5.2', 'unicode source oracle build differs')
            author = curves.CurveAuthor(controller.app, rec, Swapp)
            author.model, errors, warnings = rec.call('open locked disclosed unicode source',
                controller.open, source, read_only=False)
            result['open'] = [errors, warnings]
            curves.require(author.model is not None and errors == warnings == 0
                and Path(author.get(author.model, 'GetPathName')).samefile(source),
                'unicode source did not open cleanly at its exact path')
            result['initial'] = measure(author, case, False)
            expected_geometry(author, result['initial'], case)
            if previous is None:
                curves.require(result['initial']['body_name'] == 'AnchorBoss',
                               'disclosed source has an unexpected initial body label')
                curves.require(author.get(author.model, 'ForceRebuild3', False), 'baseline unicode source did not rebuild')
                result['baseline'] = measure(author, case, False)
                result['baseline_sha256'] = save(author, controller, folder / 'Baseline.SLDPRT')
                author.set(find_body(author), 'Name', case['body_name'])
                result['assigned'] = measure(author, case, False)
                compare(author, result['baseline'], result['assigned'], case)
                author.get(author.get(author.model, 'FeatureManager'), 'UpdateFeatureTree')
                curves.require(author.get(author.model, 'ForceRebuild3', False), 'unicode rename did not rebuild')
                result['renamed'] = measure(author, case, False)
                compare(author, result['baseline'], result['renamed'], case)
                result['renamed_sha256'] = save(author, controller, folder / 'Renamed.SLDPRT')
            else:
                compare(author, previous['renamed'], result['initial'], case)
                curves.require(author.get(author.model, 'ForceRebuild3', False), 'reopened unicode name did not rebuild')
                result['rebuilt'] = measure(author, case, False)
                compare(author, previous['renamed'], result['rebuilt'], case)
                result['reopened_sha256'] = save(author, controller, folder / 'Reopened.SLDPRT')
            result['passed'] = True
        except Exception as error:
            result['exception'] = repr(error)
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result['controller_diagnostics'] = controller.diagnostics
    result.update(source_immutable=curves.digest(source) == checksum,
                  dialogs=dialogs.log, progress_windows=dialogs.progress)
    result['passed'] = bool(result['passed'] and result['source_immutable']
        and not result['dialogs'] and not result.get('controller_diagnostics')
        and not rec.data['cleanup_errors'])
    rec.data.update(passed=result['passed'], numeric_check_count=len(rec.data['checks']))
    rec.flush()
    return result | {'record_sha256': curves.digest(rec.path)}


def run(packet, expected):
    curves.require(os.name == 'nt', 'unicode source authoring requires the root-owned Windows COM oracle')
    job = verify(packet, expected)
    root = packet.parent
    output = root / 'Inspection'
    output.mkdir()
    report = {'schema': SCHEMA, 'packet_sha256': expected, 'controls': [],
        'cases': [], 'passed': False, 'heldout_inputs_read': 0, 'writer_output_count': 0}

    def checkpoint():
        curves.write_json(output / 'Result.json', report)

    try:
        before = control_phase(output, 'ControlBefore', root / 'Control.SLDPRT')
        report['controls'].append(before)
        checkpoint()
        if before['passed']:
            for case in job['cases']:
                author = phase(output / case['name'] / 'Author', root / case['source'],
                               case['source_sha256'], case)
                row = {'name': case['name'], 'author': author}
                report['cases'].append(row)
                checkpoint()
                if author['passed']:
                    row['fresh'] = phase(output / case['name'] / 'Fresh',
                        output / case['name'] / 'Author' / 'Renamed.SLDPRT',
                        author['renamed_sha256'], case, previous=author)
                checkpoint()
    finally:
        after = control_phase(output, 'ControlAfter', root / 'Control.SLDPRT')
        report['controls'].append(after)
        verify(packet, expected)
        phases = report['controls'] + [value for row in report['cases']
                                       for key, value in row.items() if key in ('author', 'fresh')]
        births = {(item['process_id'], item['process_creation_filetime'])
                  for value in phases if (item := value.get('oracle_identity'))}
        report.update(controls_healthy=len(report['controls']) == 2
            and all(value['passed'] for value in report['controls'])
            and control_match(*report['controls']),
            distinct_processes=len(births), frozen_inputs_unchanged=True)
        report['passed'] = report['controls_healthy'] and len(phases) == len(births) == 8
        report['passed'] = report['passed'] and all(value['passed'] for value in phases)
        checkpoint()
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
