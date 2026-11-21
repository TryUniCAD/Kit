from __future__ import annotations

from argparse import ArgumentParser
from math import isfinite
from pathlib import Path
import json
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from AuthorCurves import Recorder, digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, PARAMETERS, RectangleAuthor, control
from MaterialSourceFacts import apply_material, appearance_contrast, observe, preserved_model, verify_density

SCHEMA = 'kit.sw2026.assigned-material-native-source.v1'
TOOLS = {'AuthorAssignedMaterials.py', 'MaterialSourceFacts.py', 'AuthorCurves.py',
         'AuthorRectangleAnchors.py', 'InspectFresh.py', 'OracleIdentity.py', 'Swapp.py'}
PHASES = ('Author', 'Swap', 'Depth', 'Reopen')


def checked(root, name, expected):
    relative = Path(name)
    require(not relative.is_absolute() and '..' not in relative.parts, 'material packet path escapes')
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root)
            and digest(path) == expected, 'material input custody differs: ' + str(name))
    return path


def verify(packet, expected, runtime=False):
    root = packet.parent.resolve(strict=True)
    job = json.loads(checked(root, packet.name, expected).read_bytes())
    require(job['schema'] == SCHEMA and job['oracle_sha256'] == ORACLE and job['control_sha256'] == CONTROL
            and job['writer_outputs'] == job['heldout_inputs_read_by_preparer'] == 0,
            'material source job identity/scope differs')
    require(job['cohort_role'] in ('discovery', 'sealed_original') and set(job['tools_sha256']) == TOOLS
            and Path(__file__).resolve().parent == root / 'Tools', 'material source tool closure differs')
    for name, sha in job['tools_sha256'].items():
        checked(root, 'Tools/' + name, sha)
    seed = checked(root, 'Control.SLDPRT', CONTROL)
    checked(root, 'CatalogMetadata01.json', job['catalog_metadata_sha256'])
    checked(root, 'WrapperShape01.json', job['wrapper_shape_sha256'])
    cases = job['cases']
    require(len(cases) == 2 and tuple(row['kind'] for row in cases) == ('corner', 'center')
            and len({row['id'] for row in cases}) == 2, 'two independent origin-owned source designs required')
    require(set(job['materials']) == {'A', 'B'}, 'two explicit material identities required')
    for key, material in job['materials'].items():
        require(material['key'] == key and material['name'] and '|' not in material['name']
                and type(material['density_si_hypothesis']) is float and material['density_si_hypothesis'] > 0
                and isfinite(material['density_si_hypothesis']) and material['density_si_scale_hypothesis'] == 1.0
                and material['source_property'] == 'physicalproperties/DENS/@value',
                'material source hypothesis differs')
        if runtime:
            require(digest(Path(material['database_path'])) == material['database_sha256'],
                    'installed assignment database changed after metadata freeze')
    for case in cases:
        intent = checked(root, 'Intent/' + case['id'] + '.json', job['case_intent_sha256'][case['id']])
        require(json.loads(intent.read_bytes()) == case, 'source intent differs from the packet case')
        require(case['configuration'] == 'Default' and case['first_material_key'] != case['second_material_key']
                and {case['first_material_key'], case['second_material_key']} == {'A', 'B'}, 'material case selection differs')
        require(all(type(case[name]) is float and isfinite(case[name]) and 0.001 < case[name] < 0.25
                    for name in ('width_m', 'height_m', 'depth_m', 'edited_depth_m'))
                and case['depth_m'] != case['edited_depth_m'], 'material prism inputs exceed the explicit profile')
    return root, job, seed


def save(author, controller, target):
    require(not target.exists(), 'material source output already exists')
    author.get(author.model, 'SetSaveFlag')
    result = author.rec.call('save separately authored material source', controller.save_as, author.model, target)
    require(result == (True, 0, 0) and target.is_file() and target.stat().st_size > 0,
            'native material source save failed or warned')
    return {'path': str(target), 'sha256': digest(target), 'bytes': target.stat().st_size, 'diagnostics': list(result)}


def phase(directory, case, role, materials, source=None, prior=None):
    import Swapp
    from OracleIdentity import application_identity

    directory.mkdir(parents=True, exist_ok=False)
    rec = Recorder(directory / 'Record.json', {'case': case, 'phase': role, 'writer_outputs': 0})
    result = {'passed': False, 'states': {}, 'identity': None}
    rec.data['result'] = result
    controller = author = None
    source_hash = digest(source) if source is not None else None
    first, second = [materials[case[name]] for name in ('first_material_key', 'second_material_key')]
    depth = case['edited_depth_m'] if role == 'Reopen' else case['depth_m']
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call('guard exact material source oracle idle', Swapp.sweep)
            controller = rec.call('start fresh exact material source oracle', Swapp.Sw)
            identity = rec.call('bind exact source executable', application_identity, controller.app)
            require(identity['sha256'] == ORACLE and identity['version_matches'] and controller.revision == '34.5.2',
                    'material source executable differs')
            result['identity'] = identity
            author = RectangleAuthor(controller.app, rec, Swapp)
            if role == 'Author':
                author.build(controller, case)
                base = observe(author, case, depth)
                result['states']['unassigned'] = base
                require(base['part_material'] == {'material': '', 'database': ''}, 'fresh source already has assigned material')
                contrasted = appearance_contrast(author, base, case)
                result['states']['appearance_contrast'] = contrasted
                apply_material(author, first, case['configuration'])
                assigned = observe(author, case, depth)
                result['states']['assigned'] = assigned
                verify_density(author, assigned, first, case, depth)
                preserved_model(author, base, assigned)
                require(abs(assigned['mass']['mass'] - base['mass']['mass']) > 0.01 * base['mass']['mass'],
                        'assignment did not produce a discriminating physical mass response')
                result['file'] = save(author, controller, directory / 'Original.SLDPRT')
                final = observe(author, case, depth)
                result['states']['after_save'] = final
                verify_density(author, final, first, case, depth)
                preserved_model(author, assigned, final)
            else:
                require(source is not None and prior is not None and digest(source) == prior['file']['sha256'],
                        'material reopen input differs')
                author.model, error, warning = rec.call('open exact prior material source', controller.open, source,
                                                        read_only=role == 'Reopen')
                result['open_diagnostics'] = [error, warning]
                require(author.model is not None and error == warning == 0
                        and Path(author.get(author.model, 'GetPathName')).samefile(source), 'material source reopen failed or warned')
                current = observe(author, case, depth)
                result['states']['before'] = current
                verify_density(author, current, first if role == 'Swap' else second, case, depth)
                preserved_model(author, prior['states']['after_save'], current)
                if role == 'Swap':
                    apply_material(author, second, case['configuration'])
                    after = observe(author, case, depth)
                    result['states']['changed'] = after
                    verify_density(author, after, second, case, depth)
                    preserved_model(author, current, after)
                    rec.close_number('independent material-swap mass ratio', after['mass']['mass'] / current['mass']['mass'],
                                     second['density_si_hypothesis'] / first['density_si_hypothesis'])
                    result['file'] = save(author, controller, directory / 'Swapped.SLDPRT')
                elif role == 'Depth':
                    author.edit(PARAMETERS[-1], case['edited_depth_m'])
                    depth = case['edited_depth_m']
                    after = observe(author, case, depth)
                    result['states']['changed'] = after
                    verify_density(author, after, second, case, depth)
                    rec.close_number('independent depth-change mass ratio', after['mass']['mass'] / current['mass']['mass'],
                                     depth / case['depth_m'])
                    rec.close_number('independent depth-change volume ratio', after['mass']['volume'] / current['mass']['volume'],
                                     depth / case['depth_m'])
                    result['file'] = save(author, controller, directory / 'DepthEdit.SLDPRT')
                else:
                    require(role == 'Reopen', 'unknown material source phase')
                final = observe(author, case, depth)
                result['states']['after_save'] = final
                verify_density(author, final, second, case, depth)
                if role != 'Reopen':
                    preserved_model(author, after, final)
            require(author.get(author.get(author.model, 'Extension'), 'GetWhatsWrongCount') == 0,
                    'material source accumulated native diagnostics')
            result['passed'] = True
        except Exception as error:
            rec.failure(error)
            result['error'] = repr(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                        author.model = None
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result['controller_diagnostics'] = controller.diagnostics
    if source is not None:
        result['input_sha256_before'] = source_hash
        result['input_sha256_after'] = digest(source)
        if result['input_sha256_before'] != result['input_sha256_after']:
            result['passed'] = False
            result['input_mutated'] = True
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress, numeric_checks=len(rec.data['checks']))
    result['passed'] = bool(result['passed'] and not result['dialogs'] and not rec.data['cleanup_errors']
                            and not result.get('controller_diagnostics'))
    rec.data.update(result=result, passed=result['passed'])
    rec.flush()
    return result | {'record_sha256': digest(rec.path)}


def run(packet, expected):
    require(os.name == 'nt', 'native source authoring belongs to the root Windows oracle')
    root, job, seed = verify(packet, expected, runtime=True)
    output = root / 'Inspection'
    output.mkdir(exist_ok=False)
    result = {'schema': SCHEMA, 'passed': False, 'phases': {}, 'packet_sha256': expected,
              'cohort_role': job['cohort_role'], 'writer_outputs': 0, 'qualified_writer': False,
              'heldout_credit': 0, 'source_lock': {'originals': []}}
    def add(name, row):
        result['phases'][name] = row
        write_json(output / 'Result.json', result)
    try:
        add('ControlBefore', control(output, 'ControlBefore', seed))
        if result['phases']['ControlBefore']['passed']:
            for case in job['cases']:
                prior = None
                for role in PHASES:
                    source = Path(prior['file']['path']) if prior is not None else None
                    row = phase(output / case['id'] / role, case, role, job['materials'], source, prior)
                    add(case['id'] + '/' + role, row)
                    if role == 'Author' and row['passed']:
                        result['source_lock']['originals'].append({'case_id': case['id'], 'source': row['file'],
                                                                  'request_sha256': job['case_intent_sha256'][case['id']],
                                                                  'observation_sha256': row['record_sha256']})
                        write_json(output / 'SourceLock.json', result['source_lock'])
                    if not row['passed']:
                        break
                    prior = row
    finally:
        add('ControlAfter', control(output, 'ControlAfter', seed))
    verify(packet, expected, runtime=True)
    phases = result['phases']
    identities = [row.get('identity', row.get('oracle_identity')) for row in phases.values()]
    distinct = {(row['process_id'], row['process_creation_filetime']) for row in identities if row is not None}
    result['distinct_native_processes'] = len(distinct)
    result['controls_healthy'] = all(phases[name]['passed'] for name in ('ControlBefore', 'ControlAfter'))
    result['source_lifecycle_qualified'] = len(phases) == len(distinct) == 10 and all(row['passed'] for row in phases.values())
    result['passed'] = result['source_lifecycle_qualified']
    result['density_si_hypothesis_confirmed_for_sources'] = result['passed']
    result['originals_locked'] = len(result['source_lock']['originals']) == 2
    write_json(output / 'Result.json', result)
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument('action', choices=('verify', 'run'))
    parser.add_argument('packet', type=Path)
    parser.add_argument('--packet-sha256', required=True)
    args = parser.parse_args()
    if args.action == 'verify':
        root, _, _ = verify(args.packet, args.packet_sha256)
        require(not (root / 'Inspection').exists(), 'new source output directory required')
        print(json.dumps({'passed': True, 'native_processes': 0, 'writer_outputs': 0}))
        return 0
    result = run(args.packet, args.packet_sha256)
    print(json.dumps({'passed': result['passed'], 'native_processes': result['distinct_native_processes'],
                      'writer_outputs': 0, 'originals_locked': result['originals_locked']}))
    return 0 if result['passed'] else 3


if __name__ == '__main__':
    raise SystemExit(main())
