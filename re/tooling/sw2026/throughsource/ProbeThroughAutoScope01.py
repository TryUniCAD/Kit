from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import sys
from time import time


HERE = Path(__file__).resolve()
SHARED = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover')
GUEST = PureWindowsPath(r'\\Mac\Home\Documents\UniCAD\Oracle121Takeover')
PACKET = 'ThroughAutoScope01'
DISCLOSED = 'GeneratedThroughAllSelected01'
TRIAL = '2b3474ad32783ef4c3fc0e611651772c1012b80226e4ed7501e7adcac69fc46a'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
BUILD = '34.5.2.0604'
PHASES = ('Before', 'Author', 'Reopen', 'Selected', 'After')
SCHEMA = 'kit.sw2026.disclosed-through-all-auto-scope.v1'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def checked(path, pin):
    need(path.is_file() and not path.is_symlink(), 'missing or redirected input: ' + path.name)
    data = path.read_bytes()
    need(digest(data) == pin, 'input hash mismatch: ' + path.name)
    return data


def publish(path, value):
    data = wire(value)
    with path.open('xb') as output:
        output.write(data)
    return digest(data)


def disclosed(root):
    trial = json.loads(checked(root / 'Trial02.json', TRIAL))
    for name in ('ControlCase.json', 'GeneratedCase.json', trial['control_file'], trial['generated_file']):
        checked(root / name, trial['files_sha256'][name])
    for name, pin in trial['tools_sha256'].items():
        checked(root / 'Tools' / name, pin)
    return trial


def freeze():
    need(os.name != 'nt', 'freeze the open observation inputs on the macOS host')
    disclosed(SHARED / DISCLOSED)
    root = SHARED / PACKET
    root.mkdir(mode=0o700, exist_ok=False)
    source = HERE.read_bytes()
    with (root / HERE.name).open('xb') as output:
        output.write(source)
    manifest = {'schema': SCHEMA, 'guest': str(GUEST / PACKET), 'phases': PHASES,
                'disclosed_trial_sha256': TRIAL, 'tool_sha256': digest(source)}
    return {'freeze_sha256': publish(root / 'Freeze.json', manifest), 'sealed_payloads_read': 0}


def scope(author):
    feature = author.feature('ThroughFeature')
    data = author.typed(author.get(feature, 'GetDefinition'), 'ExtrudeFeatureData2')
    scoped = bool(author.get(data, 'FeatureScope'))
    return {'feature_scope': scoped, 'auto_select': bool(author.get(data, 'AutoSelect')) if scoped else None}


def measure(folder, phase, trial_root, trial):
    import Swapp
    import ThroughAllApiMetadata as api
    from AuthorCurves import Recorder
    from InspectSelectedThroughAll import snapshot, ui_tree
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from ThroughAllAuthor import ThroughAllAuthor
    from ThroughAllSourcePlan import disclosed_cases

    api.MEMBERS = {**api.MEMBERS, 'IExtrudeFeatureData2': (*api.MEMBERS['IExtrudeFeatureData2'], 'FeatureScope', 'AutoSelect')}
    metadata = api.metadata()['interfaces']['IExtrudeFeatureData2']['members']
    getters = [row for row in metadata if row['names'][0] in ('FeatureScope', 'AutoSelect') and row['invoke_kind'] == 2]
    need({row['names'][0] for row in getters} == {'FeatureScope', 'AutoSelect'}, 'registered scope getters are absent')
    stage = folder / phase
    stage.mkdir(exist_ok=False)
    record = Recorder(stage / 'Record.json', {'schema': SCHEMA, 'phase': phase})
    selected = phase == 'Selected'
    case_name = 'GeneratedCase.json' if selected else 'ControlCase.json'
    case = json.loads(checked(trial_root / case_name, trial['files_sha256'][case_name]))
    item = trial['generated_file' if selected else 'control_file']
    path = trial_root / item
    expected = trial['files_sha256'][item]
    saved = folder / 'Author/NativeAutoScope.SLDPRT'
    if phase == 'Reopen':
        author_result = json.loads((folder / 'Author/Record.json').read_bytes())
        need(author_result['passed'], 'fresh reopen requires a successful author and save')
        path, expected = saved, author_result['result']['saved_sha256']
    original = phase != 'Author'
    result = {'passed': False, 'scope_getters': getters, 'input_sha256': expected if original else None}
    controller = author = None
    with AssemblyLoadMonitor() as monitor:
        try:
            if original:
                checked(path, expected)
            record.call('verify the serial native oracle is idle', Swapp.sweep)
            controller = record.call('start the pinned native scope observer', Swapp.Sw)
            identity = record.call('verify the native executable', application_identity, controller.app)
            need(identity['version_matches'] and identity['file_version'] == BUILD and identity['sha256'] == ORACLE,
                 'the installed native build changed')
            result['native_identity'] = identity
            author = ThroughAllAuthor(controller.app, record, Swapp)
            if original:
                model, errors, warnings = record.call('open the disclosed part read only', controller.open, path, read_only=True)
                author.model = model
                result['open'] = [model is not None, errors, warnings]
                need(result['open'] == [True, 0, 0] and Path(author.get(model, 'GetPathName')).samefile(path),
                     'disclosed open did not select the requested part cleanly')
            else:
                native_case = disclosed_cases()[0]
                need(native_case['id'] == 'D01', 'the disclosed author recipe changed')
                author.build(native_case, controller)
                result['author_arguments'] = record.data['source_authoring']
            result['initial'] = scope(author)
            before = snapshot(author, case, edited=False, rebuild=False)
            rebuilt = snapshot(author, case, edited=False, rebuild=True)
            result['rebuilt'] = scope(author)
            need(ui_tree(before) == ui_tree(rebuilt) and record.data['checks'] and all(row['passed'] for row in record.data['checks']),
                 'scope readback changed the validated native tree or shape')
            if not original:
                result['save'] = list(record.call('save the owned automatic scope part', controller.save_as, author.model, saved))
                need(result['save'] == [True, 0, 0] and saved.is_file(), 'automatic scope save warned or failed')
                result['saved_sha256'] = digest(saved.read_bytes())
                result['after_save'] = scope(author)
            result['passed'] = True
        except Exception as error:
            record.failure(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        record.call('close the owned scope document', controller.close_doc, author.model)
                except Exception as error:
                    record.failure(error, cleanup=True)
                try:
                    controller.close()
                except Exception as error:
                    record.failure(error, cleanup=True)
                result['controller_diagnostics'] = controller.diagnostics
    result['input_immutable'] = not original or (path.is_file() and digest(path.read_bytes()) == expected)
    result['dialogs'] = monitor.log
    result['passed'] = bool(result['passed'] and result['input_immutable'] and not result['dialogs']
                            and not result.get('controller_diagnostics') and record.data['first_failure'] is None)
    record.data.update(result=result, passed=result['passed'], finished_at=time())
    record.flush()
    return {'phase': phase, 'passed': result['passed'], 'record_sha256': digest(record.path.read_bytes())}


def summarize(folder):
    rows, hashes = {}, {}
    for phase in PHASES:
        raw = (folder / phase / 'Record.json').read_bytes()
        rows[phase] = json.loads(raw)
        hashes[phase] = digest(raw)
    results = {phase: row['result'] for phase, row in rows.items()}
    need(results['Before']['passed'] and results['After']['passed'], 'the scope experiment has no healthy bracket')
    ticks = {row['native_identity']['process_creation_filetime'] for row in results.values() if 'native_identity' in row}
    ordered = tuple(rows.values())
    serial = all(a['finished_at'] <= b['started_at'] for a, b in zip(ordered, ordered[1:]))
    passed = all(row['passed'] for row in results.values()) and len(ticks) == len(PHASES) and serial
    value = {'schema': SCHEMA, 'passed': passed, 'phase_receipt_sha256': hashes, 'distinct_processes': len(ticks),
             'observed_scopes': {name: {key: row[key] for key in ('initial', 'rebuilt', 'after_save') if key in row} for name, row in results.items()},
             'scope_getters': results['Before']['scope_getters'], 'sealed_payloads_read': 0, 'multibody_selection_measured': False}
    return value | {'receipt_sha256': publish(folder / 'Result.json', value)}


def main():
    parser = ArgumentParser()
    modes = parser.add_subparsers(dest='mode', required=True)
    modes.add_parser('freeze')
    for name in ('phase', 'summary'):
        mode = modes.add_parser(name)
        mode.add_argument('manifest', type=Path)
        mode.add_argument('pin')
        if name == 'phase':
            mode.add_argument('phase', choices=PHASES)
    args = parser.parse_args()
    if args.mode == 'freeze':
        result = freeze()
    else:
        need(os.name == 'nt', 'run the actual scope observation inside the Windows guest')
        manifest = json.loads(checked(args.manifest, args.pin))
        root = args.manifest.parent
        need(manifest['schema'] == SCHEMA and manifest['guest'] == str(root) and list(PHASES) == manifest['phases']
             and manifest['disclosed_trial_sha256'] == TRIAL and HERE == root / HERE.name
             and digest(HERE.read_bytes()) == manifest['tool_sha256'], 'scope packet identity differs')
        trial_root = root.with_name(DISCLOSED)
        trial = disclosed(trial_root)
        sys.path.insert(0, str(trial_root / 'Tools'))
        folder = Path('C:/KitSdkCandidates') / PACKET
        need(folder.resolve() == folder and not folder.is_symlink(), 'scope output directory is redirected')
        folder.mkdir(exist_ok=True)
        if args.mode == 'phase':
            if args.phase not in ('Before', 'After'):
                before = json.loads((folder / 'Before/Record.json').read_bytes())
                need(before['passed'], 'the initial disclosed control did not pass')
            result = measure(folder, args.phase, trial_root, trial)
        else:
            result = summarize(folder)
    sys.stdout.buffer.write(wire(result))
    return int(result.get('passed') is False)


if __name__ == '__main__':
    raise SystemExit(main())
