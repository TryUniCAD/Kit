from argparse import ArgumentParser
from base64 import b64decode, b64encode
import codecs
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve()
HOST = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover')
GUEST = PureWindowsPath(r'\\Mac\Home\Documents\UniCAD\Oracle121Takeover')
DISCLOSED = 'GeneratedThroughAllSelected01'
TRIAL_PIN = '2b3474ad32783ef4c3fc0e611651772c1012b80226e4ed7501e7adcac69fc46a'
NATIVE_RECEIPT_PIN = '08548697827331a861c15769a5c9a2e347aa3500e6c708f334807cac0de21632'
SOURCE_RECEIPT_PIN = 'e2ce5101c7e703747400c29ff2a29be09dfe21007b4a602789f052e692b835f3'
REVISION = '6803987defeb0e69e39542b05eaa3618aefb46ff'
ARMS = ('Present', 'Absent')
SCHEMA = 'kit.sw2026.disclosed-stock-inactive-secondary-calibration.v1'
OWNER = 'StockBoss.f818.f20'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), 'missing or redirected frozen file: ' + path.name)
    data = path.read_bytes()
    require(digest(data) == expected, 'frozen digest changed: ' + path.name)
    return data


def publish(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as output:
        output.write(data)
    return digest(data)


def compare_graph(left, right, left_end, right_end):
    seen_left, seen_right, changes = {}, {}, []

    def compare(a, b):
        require(type(a) is type(b), 'unrelated typed field changed its wire kind')
        if hasattr(a, 'FieldsValue'):
            if id(a) in seen_left or id(b) in seen_right:
                require(seen_left.get(id(a)) is b and seen_right.get(id(b)) is a, 'unrelated typed object alias changed')
                return
            seen_left[id(a)], seen_right[id(b)] = b, a
            require(a.ClassValue == b.ClassValue, 'unrelated class or schema changed')
            if a is left_end:
                require(b is right_end and a.FieldsValue['f20'] is not None and b.FieldsValue['f20'] is None,
                        'removed display does not belong to the corresponding actual stock')
                changes.append(OWNER)
                compare({key: value for key, value in a.FieldsValue.items() if key != 'f20'},
                        {key: value for key, value in b.FieldsValue.items() if key != 'f20'})
            else:
                compare(a.FieldsValue, b.FieldsValue)
        elif isinstance(a, dict):
            require(a.keys() == b.keys(), 'unrelated typed field keys changed')
            for key in a:
                compare(a[key], b[key])
        elif isinstance(a, (tuple, list)):
            for x, y in zip(a, b, strict=True):
                compare(x, y)
        else:
            require(a == b, 'unrelated typed field value changed')

    compare(left, right)
    require(changes == [OWNER], 'expected exactly one typed owner change')
    return changes


def worker(code, tools):
    recipe = json.load(sys.stdin)
    sys.path[:0] = [str(code / 'src'), str(tools)]
    from convert import open_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Construction.BodyScope.FinishScopePart import FinishScopePart
    from convert.adapters.solidworks.Archive.Construction.BodyScope.SelectedStock import SelectedStock
    from convert.adapters.solidworks.Archive.Construction.BodyScope.SelectStockMut import SelectStockMut
    from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import CircleInput
    from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeScopedThru import MakeScopedThru
    from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThroughPart import MakeThroughPart
    from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import ThroughEndInput
    from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import ThroughPartSpec
    from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import ThroughStock
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
    from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadColdSelectedStock import ReadColdStock
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutBodyLink import ReadCutBodyLink
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from SdkNativeRoundTrips import roundtrips

    for encoding in ('ascii', 'latin-1', 'utf-8', 'utf-8-sig', 'utf-16-le', 'utf-16-be'):
        codecs.lookup(encoding)
    for module in ('interchange.brep.Validation.BrepValidate', 'interchange.document.Behavior.DocumentIo',
                   'interchange.document.Models.DocumentProvenance', 'interchange.document.Validation.DocumentAssemblyValidate',
                   'interchange.document.Validation.DocumentFeatureValidate', 'interchange.document.Validation.DocumentReferenceValidate'):
        import_module(module)
    attempts = []

    def audit(event, args):
        if event in {'open', 'os.listdir', 'os.scandir', 'os.system', 'os.exec', 'os.fork', 'os.posix_spawn', 'os.startfile'} or event.startswith(('subprocess.', 'socket.', 'ctypes.', 'winreg.')):
            attempts.append(event)
            raise PermissionError('model-only worker attempted external access: ' + event)

    sys.addaudithook(audit)
    require(recipe['axis'] == 'z' and recipe['direction'] == 'forward' and recipe['configuration'] == 'Default',
            'calibration is restricted to the disclosed forward Front cut')
    width, height, depth = recipe['stock_size_m']
    cx, cy = recipe['stock_center_m']
    vertices = tuple((cx + u * width / 2, cy + v * height / 2) for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)))
    stock = ThroughStock(recipe['name'], recipe['configuration'], 'Front Plane', 'stock-sketch', 'StockProfile',
                         'stock-boss', 'StockBoss', 'stock-depth', 'cut-body', vertices, depth, width, height, 'z')
    plan = ThroughPartSpec(stock, CircleInput(tuple(recipe['circle_center_m']), recipe['radius_m'], 19000),
                           'ThroughProfile', 'ThroughFeature', ThroughEndInput('through_all', True, 19000))
    recipe_value = MakePartRecipe(stock, recipe['written_at'])
    output = FinalPartPath(BytesIO(), WriteOptions(values={'final_destination': recipe['native_path']}),
                           recipe_value.OutputValue, stock.NameValue)
    inputs = replace(recipe_value, OutputValue=output)
    scope = SelectedStock((stock,), 'selected', 19000)
    unchanged = MakeScopedThru(plan, inputs, scope).PartValue.BytesValue
    inspections, results = [], {}

    for name in ARMS:
        candidate = MakeThroughPart(plan, inputs)
        owners = SelectStockMut(candidate, scope)
        end = candidate.BossValue.EndValue
        primary, secondary, *_ = candidate.BossValue.DimensionsValue
        require(owners.FeatureValue is candidate.BossValue.FeatureValue
                and owners.FeatureValue.FieldsValue['f818'] is end
                and (end.FieldsValue['f08'], end.FieldsValue['f0c'], end.FieldsValue['f10'], end.FieldsValue['f8c']) == (1, 6, 0, 0)
                and end.FieldsValue['f18'] is primary.DisplayValue and end.FieldsValue['f20'] is secondary.DisplayValue
                and primary.ParameterValue is not secondary.ParameterValue
                and primary.ParameterValue.FieldsValue['f58'] == secondary.ParameterValue.FieldsValue['f58'] == depth,
                'wrong stock, end mode or constructor-only display owners')
        if name == 'Absent':
            end.FieldsValue['f20'] = None
        candidate = FinishScopePart(candidate, inputs)
        data = candidate.BytesValue
        require((data == unchanged) == (name == 'Present'), 'normal control is no longer exactly the unchanged narrow SDK output')
        archive = SldprtArchive.from_bytes(data)
        link, _, _, _, streams = roundtrips(archive, False)
        require(len(streams) == 10 and ReadFileKey(link.ConfigValue.HeaderValue.FieldsValue['f38'])[1] == recipe['native_path'],
                'complete assembly of the part or exact encoded locator differs')
        roots = link.ResolvedValue.RootsValue
        features = {NativeNodeId(node): node for node in roots}
        boss = ReadExtrude(link, roots[-3], features)
        cut = ReadExtrude(link, roots[-1], features, IsCut=True)
        atom, atom_id = ReadColdStock(link, boss.NodeValue, cut.NodeValue)
        require(boss.SecondValue is None and boss.SecondModeValue is None and cut.DepthValue is None and cut.SecondValue is None
                and boss.RequireDepth().DepthValue.native_value == depth and boss.RequireDepth().DepthValue.name == 'D1',
                'actual active stock or depthless cut semantics changed')
        reverse = boss.EndValue.FieldsValue['f20']
        if name == 'Present':
            second = ReadDepthOwner(link, reverse, 'f20')
            require(second.Parameter is not boss.RequireDepth().Parameter and second.DepthValue.name == 'D2'
                    and second.DepthValue.native_value == depth, 'baseline lost its independent initialized role')
        else:
            require(reverse is None, 'absent variant still has its secondary display')
        try:
            body_link = ReadCutBodyLink(link, features, boss, cut)
        except ValueError as error:
            body_link = {'refusal': str(error)}
        try:
            document = open_document(data, source_format='solidworks.sldprt', strict=True, include_tessellation=False)
            document.assert_valid()
        except SldprtFormat as error:
            require(str(error) == 'SLDPRT contains no readable Parasolid payload', 'strict geometry refused for an unrelated reason')
            strict_geometry, public_refusal = False, str(error)
        else:
            strict_geometry, public_refusal = document.brep is not None, None
        require(strict_geometry == (name == 'Present'), 'expected the unchanged strict cold geometry distinction')
        require(body_link.get('binding') == 'cold_selected_stock_atom' if name == 'Present'
                else body_link == {'refusal': 'typed model expected concrete schema one moDisplayDistanceDim_c'},
                'unchanged selected-stock guard refused at a different owner')
        maps = (link.ConfigValue.MapValue, link.ResolvedValue.MapValue)
        require(maps[0].CounterValue == link.ResolvedValue.MapBase, 'linked archive map did not preserve its prefix')
        classes = Counter(entry.EntryValue.ClassValue.NameValue for entry in maps[1].EntriesValue if hasattr(entry.EntryValue, 'FieldsValue'))
        inspections.append((link, boss.EndValue, classes))
        results[name] = {'sha256': digest(data), 'bytes': len(data), 'stream_roundtrips': streams,
                         'config_map_next': maps[0].CounterValue, 'resolved_map_next': maps[1].CounterValue,
                         'readback_f20_m': depth if reverse is not None else None, 'stock_atom_id': atom_id,
                         'actual_stock_atom_owner': atom.FieldsValue['f140'] == atom_id,
                         'strict_sdk_geometry': strict_geometry, 'strict_body_link': body_link,
                         'strict_public_refusal': public_refusal, 'matches_unmodified_sdk': data == unchanged,
                         'artifact': b64encode(data).decode()}

    def roots(link):
        return (link.ConfigValue.RootValue, link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields)

    (a, stock_a, classes_a), (b, stock_b, classes_b) = inspections
    changed = compare_graph(roots(a), roots(b), stock_a, stock_b)
    a_streams, b_streams = (results[name]['stream_roundtrips'] for name in ARMS)
    stream_delta = {key: [a_streams[key]['bytes'], b_streams[key]['bytes']] for key in a_streams if a_streams[key] != b_streams[key]}
    lost = classes_a - classes_b
    require(lost and not (classes_b - classes_a) and a_streams.keys() == b_streams.keys() and not attempts,
            'scope contrast added a typed vertex, changed stream inventory or attempted runtime access')
    return {'arms': results, 'graph_differences': changed, 'lost_map_objects': dict(lost), 'stream_length_changes': stream_delta,
            'runtime_external_accesses': len(attempts), 'native_acceptance': False, 'heldout_credit': 0}


def freeze(name):
    require(os.name != 'nt' and re.fullmatch(r'MidPlaneStockSecondary[0-9]{2}', name), 'choose an unused disclosed host packet')
    target = HOST / name
    require(not target.exists() and target.resolve() == target, 'calibration packet exists or is redirected')
    repo = HERE.parents[4]
    base = HOST / DISCLOSED
    trial = json.loads(checked(base / 'Trial02.json', TRIAL_PIN))
    files = {f'Tools/{file}': checked(base / 'Tools' / file, pin) for file, pin in trial['tools_sha256'].items()}
    for file in ('ControlCase.json', 'GeneratedCase.json', 'NeutralRequest.json'):
        files[file] = checked(base / file, trial['files_sha256'][file])
    files['ApiMetadata.json'] = checked(base / 'ApiMetadata.json', '9d5509a9ac17bf54f30bfaa8abc6565a1bc7a2c52cf9823627bda8f88ae75f33')
    files['NativeControlReceipt.json'] = checked(repo / 're/solidworks/measurements/2026/SdkThroughAllSelectedBodyNative01.json', NATIVE_RECEIPT_PIN)
    files['NativeSourceReceipt.json'] = checked(repo / 're/solidworks/measurements/2026/ThroughAllD01ReadProcess01.json', SOURCE_RECEIPT_PIN)

    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args])

    files['Sdk.tar'] = git('archive', '--format=tar', REVISION, 'src')
    files['Tools/SdkNativeRoundTrips.py'] = git('show', REVISION + ':re/tooling/sw2026/SdkNativeRoundTrips.py')
    files['Tools/' + HERE.name] = HERE.read_bytes()
    case = json.loads(files.pop('GeneratedCase.json'))
    intent = json.loads(files.pop('NeutralRequest.json'))
    require(case['recipe'] == intent and len(case['expected_tree']) == 27 and case['heldout_payloads_read'] == 0,
            'disclosed neutral lifecycle descriptor differs')
    control = trial['control_file']
    control_pin = trial['files_sha256'][control]
    checked(base / control, control_pin)
    native_root = PureWindowsPath('C:/KitSdkCandidates', name)
    intent.update(name='StockSecondaryCalibration', native_path=str(native_root / 'GeneratedInput/StockSecondaryCalibration.SLDPRT'))
    case['recipe'] = intent
    files['CandidateCase.json'] = wire(case)
    with TemporaryDirectory(prefix='KitStockSecondary-') as tmp:
        scratch = Path(tmp)
        with open_tar(fileobj=BytesIO(files['Sdk.tar']), mode='r:') as archive:
            archive.extractall(scratch / 'Code', filter='data')
        for file in ('Tools/' + HERE.name, 'Tools/SdkNativeRoundTrips.py'):
            publish(scratch / file, files[file])
        command = [sys.executable, '-I', '-B', str(scratch / 'Tools' / HERE.name), 'worker', str(scratch / 'Code')]
        first, second = (subprocess.check_output(command, input=wire(intent), timeout=120) for _ in ARMS)
    require(first == second, 'independent guarded calibration builds differ')
    proof = json.loads(first)
    for name in ARMS:
        data = b64decode(proof['arms'][name].pop('artifact'), validate=True)
        require(digest(data) == proof['arms'][name]['sha256'], 'worker output transport digest changed')
        files[f'Arms/{name}/StockSecondaryCalibration.SLDPRT'] = data
    files['BuildProof.json'] = wire(proof)
    plan = {'schema': SCHEMA, 'revision': REVISION, 'disclosed_trial_sha256': TRIAL_PIN, 'private': str(native_root),
            'guest': str(GUEST / target.name), 'control': {'path': str(GUEST / DISCLOSED / control), 'sha256': control_pin},
            'files': {name: digest(data) for name, data in files.items()}, 'native_acceptance': False, 'heldout_credit': 0}
    target.mkdir(mode=0o700, exist_ok=False)
    for file, data in files.items():
        publish(target / file, data)
    pin = publish(target / 'Freeze.json', wire(plan))
    return {'freeze': str(target / 'Freeze.json'), 'freeze_sha256': pin, 'build_sha256': digest(files['BuildProof.json']),
            'cold_geometry': {name: proof['arms'][name]['strict_sdk_geometry'] for name in ARMS}, 'heldout_credit': 0}


def native_comparison(records, depth):
    observations = {}
    for name in ARMS:
        generated = records[name, 'Generated']['result']
        reopened = records[name, 'Reopen']['result']
        require(generated['save'] == [True, 0, 0] and generated['saved_sha256'] == reopened['input_sha256'], 'owned save or reopen changed')
        observations[name] = tuple(generated[key] for key in ('initial', 'rebuilt', 'edited', 'saved')) + tuple(
            reopened[key] for key in ('initial', 'rebuilt'))
    actual = {name: [row['stock']['depth_reverse_m'] for row in rows] for name, rows in observations.items()}
    require(actual == {'Present': [depth] * 6, 'Absent': [0.0] * 6}, 'COM alternate depth differs from prospective typed-owner prediction')
    for present, absent in zip(*observations.values(), strict=True):
        for row in (present, absent):
            stock = row['stock']
            require((stock['end_forward'], stock['end_reverse'], stock['both_directions'], stock['reverse_direction']) == (6, 0, False, False)
                    and len(stock['dimensions']) == 1 and row['stock_axis_relation_types'] == [4, 4, 5, 5],
                    'active stock depth or relation owners differ')
        guards = ('configuration', 'tree', 'profiles', 'operation', 'stock_axis_relation_types', 'body_count', 'whats_wrong', 'edited')
        require(all(present[key] == absent[key] for key in guards), 'another native profile, feature or solid owner changed')
        require({key: v for key, v in present['stock'].items() if key != 'depth_reverse_m'}
                == {key: v for key, v in absent['stock'].items() if key != 'depth_reverse_m'}, 'another native stock dimension or end changed')
        a, b = (row['mass'] for row in (present, absent))
        require(all(isclose(row['mass'], row['volume'], rel_tol=2e-7) for row in (a, b))
                and all(isclose(a[key], b[key], rel_tol=2e-7) for key in ('volume', 'area', 'mass'))
                and all(isclose(x, y, rel_tol=2e-7, abs_tol=1e-10) for x, y in zip(a['com'], b['com'], strict=True)),
                'changing the inactive display changed native solid measurements')
    return actual


def observe(path, pin):
    require(os.name == 'nt', 'native calibration belongs to the Windows oracle owner')
    packet = path.parent
    plan = json.loads(checked(path, pin))
    require(plan['schema'] == SCHEMA and plan['revision'] == REVISION and plan['disclosed_trial_sha256'] == TRIAL_PIN
            and plan['guest'] == str(packet) and HERE == packet / 'Tools' / HERE.name, 'native calibration packet identity differs')
    for name, expected in plan['files'].items():
        checked(packet / name, expected)
    checked(Path(plan['control']['path']), plan['control']['sha256'])
    private = Path(plan['private'])
    require(private == Path('C:/KitSdkCandidates') / packet.name and private.resolve() == private and not private.exists(),
            'destination already exists or escaped the managed local directory')
    private.mkdir(parents=True, exist_ok=False)
    from InspectSelectedThroughAll import phase

    proof = json.loads((packet / 'BuildProof.json').read_bytes())
    case = json.loads((packet / 'CandidateCase.json').read_bytes())
    control = json.loads((packet / 'ControlCase.json').read_bytes())
    live = Path(case['recipe']['native_path'])
    require(live == private / 'GeneratedInput/StockSecondaryCalibration.SLDPRT', 'shared native self locator differs')
    publish(private / 'ApiMetadata.json', (packet / 'ApiMetadata.json').read_bytes())
    control_job = {'control_file': plan['control']['path'], 'files_sha256': {plan['control']['path']: plan['control']['sha256']}}

    try:
        before = phase(private, control_job, case, control, 'ControlBefore')
        if before:
            for name in ARMS:
                frozen_input = packet / 'Arms' / name / live.name
                expected = proof['arms'][name]['sha256']
                publish(live, checked(frozen_input, expected))
                job = {'generated_file': str(live), 'files_sha256': {str(live): expected}}
                success = phase(private, job, case, control, 'Generated')
                if success:
                    phase(private, job, case, control, 'Reopen')
                archive = private / 'Arms' / name
                archive.mkdir(parents=True, exist_ok=False)
                live.rename(archive / live.name)
                for stage in ('Generated', 'Reopen'):
                    observation = private / 'Inspection' / stage
                    if observation.exists():
                        observation.rename(archive / stage)
    finally:
        phase(private, control_job, case, control, 'ControlAfter')

    order = tuple((name, stage) for name in ARMS for stage in ('Generated', 'Reopen'))
    paths = {('Control', 'Before'): private / 'Inspection/ControlBefore/Record.json',
             **{(name, stage): private / 'Arms' / name / stage / 'Record.json' for name, stage in order},
             ('Control', 'After'): private / 'Inspection/ControlAfter/Record.json'}
    summary = {'passed': False, 'freeze_sha256': pin, 'heldout_credit': 0, 'strict_sdk_absent_admitted': False}
    summary['phase_sha256'] = {'/'.join(key): digest(path.read_bytes()) for key, path in paths.items() if path.is_file()}
    try:
        records = {key: json.loads(path.read_bytes()) for key, path in paths.items()}
        require(all(record['passed'] and record['result']['open'] == [True, 0, 0] and record['result']['input_immutable']
                    and record['checks'] and all(check['passed'] for check in record['checks']) for record in records.values()),
                'a healthy bracket or clean candidate phase failed')
        require(len({record['result']['oracle_identity']['process_creation_filetime'] for record in records.values()}) == 6,
                'native phase reused a prior process')
        require(all(records['Control', role]['result'][state]['stock']['depth_reverse_m'] == 0.0
                    for role in ('Before', 'After') for state in ('initial', 'rebuilt')), 'disclosed native source control no longer has an absent secondary display')
        summary['actual_reverse_depths_m'] = native_comparison(records, case['recipe']['stock_size_m'][2])
        summary['passed'] = True
    except (OSError, KeyError, ValueError) as error:
        summary['refusal'] = str(error)
    receipt = publish(private / 'Result.json', wire(summary))
    return {'passed': summary['passed'], 'result_sha256': receipt, 'native_process_receipts': len(summary['phase_sha256']), 'heldout_credit': 0}


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest='mode', required=True)
    commands.add_parser('freeze').add_argument('name')
    commands.add_parser('worker').add_argument('code', type=Path)
    native = commands.add_parser('observe')
    native.add_argument('freeze', type=Path)
    native.add_argument('pin')
    args = parser.parse_args()
    if args.mode == 'worker':
        result = worker(args.code, HERE.parent)
    elif args.mode == 'observe':
        result = observe(args.freeze, args.pin)
    else:
        result = freeze(args.name)
    sys.stdout.buffer.write(wire(result))
    return int(result.get('passed') is False)


if __name__ == '__main__':
    raise SystemExit(main())
