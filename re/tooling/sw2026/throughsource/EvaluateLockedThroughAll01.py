from argparse import ArgumentParser
from base64 import b64decode, b64encode
import codecs
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
import sys
from tarfile import open as open_tar


HERE = Path(__file__).resolve()
HOME = Path('/Users/odin')
SHARED = HOME / 'Documents/UniCAD/Oracle121Takeover'
SOURCE = 'ThroughAllSourcePacket03'
NATIVE = 'GeneratedThroughAllSelected01'
SOURCE_ROOT = PureWindowsPath(r'C:\KitThroughAllSource121')
SHARED_GUEST = PureWindowsPath(r'\\Mac\Home\Documents\UniCAD\Oracle121Takeover')
SOURCE_PACKET = '6ff86683ab5da1f99aab8b6efaccb978ce115a1d0d3013a73c315cb0c5d1362c'
SOURCE_SEAL = '9f6b173e0bffee91ecd3b9ef53c9a85ace59ac7323f42318b40a18a682bc2045'
SPEC = '3afff19bff54e29c7ebf1542e398baecb549f7cf51eccb759fed6a2cadd48761'
LOCK = '3efe141cd31cc06e8b7545db590548dd1ba511960261e8b78cf72523d5d5ba79'
LOCK_PATH = 're/solidworks/v2026/heldout/ThroughAllSourceLock01.json'
DISCLOSED_PACKET = '2b3474ad32783ef4c3fc0e611651772c1012b80226e4ed7501e7adcac69fc46a'
DISCLOSED_RESULT = 'f95b0c5e647d2312d483da7a0e95c4444d551705127ddea1978e9c6c405ceeeb'
DISCLOSED_METADATA = '9d5509a9ac17bf54f30bfaa8abc6565a1bc7a2c52cf9823627bda8f88ae75f33'
STOCK_PACKET = 'MidPlaneStockSecondary02'
STOCK_FREEZE = '61365d7aee925dcf5b75e6bb5b8e342bdc0a58d69be7a888e6745acf22a79c9e'
STOCK_NATIVE = 'a77fd9262fb9d92e31cdfa18778c3a9d7dd7e8543802795956ead2a6a8d65892'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
BUILD = '34.5.2.0604'
REVISION = '6803987defeb0e69e39542b05eaa3618aefb46ff'
SOURCE_COMMIT = '64993a926e5cfca468bc5ae19c3b36455d95c80b'
WRITERS = ('9179c9ca4ab0eee1a6e7aff5e4c6db126f1db8c8', 'ebaa0bb1fd415af12a7f35bc0004ad698fdb606f',
           '7fd67d22dafb5078e0b82e3d2108481641a91e41', '3233f49d57e146fb15071d45cdd75d29d6ce26e5')
SLOTS = ('H01', 'H02')
AXES = {'front': 'z', 'top': 'y', 'right': 'x'}
PHASES = ('ControlBefore', 'Generated', 'Reopen', 'ControlAfter')
SOURCE_PHASES = ('before', 'author', 'reopen-source', 'reopen-edited', 'after')
SCHEMA = 'kit.sw2026.locked-through-all-selected-stock-evaluation.v1'
CUT_SCOPE = 'explicitly selected single stock; continuous automatic source selection remains unqualified'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), 'required frozen input is absent or redirected: ' + path.name)
    data = path.read_bytes()
    require(digest(data) == expected, 'frozen input digest differs: ' + path.name)
    return data


def publish(path, data):
    with path.open('xb') as output:
        output.write(data)
    return digest(data)


def locked_case(data, slot):
    value = json.loads(data)
    pitches = tuple(row['slot'] for row in value['slots'] if row['heldout'] and row['analytic_geometry_qualified'])
    require(value['passed'] and value['packet_sha256'] == SOURCE_PACKET and value['guest_sealed_spec_sha256'] == SPEC
            and value['native_processes'] == 35 and value['healthy_controls'] == 14
            and value['writer_output_count'] == value['host_heldout_payloads_read'] == 0
            and not value['new_writer_constructed_at_source_freeze'] and not value['heldout_writer_acceptance']
            and pitches == SLOTS and slot in pitches, 'expected the unopened pre-writer analytic cut lock')
    row, = (row for row in value['slots'] if row['slot'] == slot)
    require(set(row['phase_records']) == set(SOURCE_PHASES) and set(row['native_artifacts']) == {'source', 'edited'},
            'source lifecycle custody is incomplete')
    identities = [row['phase_records'][phase]['native_identity'] for phase in SOURCE_PHASES]
    require(len({item['process_creation_filetime'] for item in identities}) == 5
            and all(item['file_version'] == BUILD and item['sha256'] == ORACLE for item in identities),
            'source lifecycle used a different build or reused a process')
    return row


def freeze(name, slot, epoch, revision=REVISION):
    require(os.name != 'nt' and re.fullmatch(r'SdkLockedThroughAll[0-9]{2}', name), 'choose an unused managed host packet')
    target = SHARED / name
    require(target.resolve() == target and not target.exists(), 'host packet already exists or is redirected')
    repo = HERE.parents[4]

    def git(*argv):
        return subprocess.run(['git', '-C', str(repo), *argv], capture_output=True, check=True).stdout

    require(re.fullmatch(r'[0-9a-f]{40}', revision) and git('cat-file', '-t', revision).strip() == b'commit',
            'freeze requires one exact SDK commit')
    git('merge-base', '--is-ancestor', REVISION, revision)
    lock_data = git('show', revision + ':' + LOCK_PATH)
    require(digest(lock_data) == LOCK, 'public source lock changed')
    row = locked_case(lock_data, slot)
    source = SHARED / SOURCE
    source_packet = json.loads(checked(source / 'Source.json', SOURCE_PACKET))
    seal = json.loads(checked(source / 'Progress/D00/seal/Record.json', SOURCE_SEAL))
    source_lock = checked(source / 'Progress' / slot / 'lock/Record.json', row['case_lock_sha256'])
    locked = json.loads(source_lock)
    require(source_packet['guest_private_base'] == str(SOURCE_ROOT) and seal['passed']
            and seal['packet_sha256'] == SOURCE_PACKET and seal['sealed_spec_sha256'] == SPEC
            and locked['passed'] and locked['heldout_source_locked'] and locked['analytic_geometry_qualified']
            and locked['case_id'] == slot and locked['native_artifacts'] == row['native_artifacts'],
            'original source packet and opaque guest seal differ')
    times = [int(git('show', '-s', '--format=%ct', commit)) for commit in (SOURCE_COMMIT, *WRITERS)]
    for commit in (SOURCE_COMMIT, *WRITERS):
        git('merge-base', '--is-ancestor', commit, revision)
    require(seal['finished_at'] < locked['finished_at'] < times[0] < min(times[1:])
            and max(times[1:]) < epoch <= 0xffffffff - 20,
            'source lock or explicit authoring epoch violates the pre-writer chronology')
    disclosed = SHARED / NATIVE
    packet = json.loads(checked(disclosed / 'Trial02.json', DISCLOSED_PACKET))
    result = json.loads(checked(disclosed / 'Inspection/Result.json', DISCLOSED_RESULT))
    require(result['passed'] and result['controls_healthy'] and result['distinct_native_processes'] == 4
            and result['numeric_checks'] == 72 and result['heldout_payloads_read'] == 0, 'the disclosed native control proof differs')
    tools = {f'Tools/{file}': checked(disclosed / 'Tools' / file, pin) for file, pin in packet['tools_sha256'].items()}
    tools['Tools/' + HERE.name] = HERE.read_bytes()
    for module in ('SdkNativeRoundTrips.py', 'throughsource/Compare.py', 'throughsource/Coverage.py', 'throughsource/Predict.py', 'throughsource/Shape.py'):
        tools['Tools/' + PurePosixPath(module).name] = git('show', revision + ':re/tooling/sw2026/' + module)
    files = tools | {file: checked(disclosed / file, packet['files_sha256'][file]) for file in ('ControlCase.json', 'GeneratedCase.json')}
    files['ApiMetadata.json'] = checked(disclosed / 'ApiMetadata.json', DISCLOSED_METADATA)
    files['SourceLock.json'] = lock_data
    files['SelectedLockRecord.json'] = source_lock
    files['Sdk.tar'] = git('archive', '--format=tar', revision, 'src')
    tree = json.loads(files.pop('GeneratedCase.json'))['expected_tree']
    require(len(tree) == 27 and tree == json.loads(files['ControlCase.json'])['expected_tree'], 'disclosed recursive tree reference differs')
    files['ExpectedTree.json'] = encode(tree)
    control_path = packet['control_file']
    control_sha = packet['files_sha256'][control_path]
    checked(disclosed / control_path, control_sha)
    private = PureWindowsPath('C:/KitSdkCandidates', name)
    plan = {'schema': SCHEMA, 'slot': slot, 'epoch': epoch, 'revision': revision, 'chronology_unix_seconds': times,
            'guest': str(SHARED_GUEST / name), 'private': str(private), 'phases': list(PHASES),
            'control': {'location': str(SHARED_GUEST / NATIVE / control_path), 'sha256': control_sha},
            'source_slot_lock_sha256': row['case_lock_sha256'], 'scope': CUT_SCOPE,
            'files': {file: digest(data) for file, data in sorted(files.items())},
            'whole_source_admitted': False, 'heldout_credit': 0}
    target.mkdir(mode=0o700, exist_ok=False)
    for file, data in files.items():
        path = target / file
        path.parent.mkdir(exist_ok=True)
        publish(path, data)
    pin = publish(target / 'Freeze.json', encode(plan))
    return {'freeze_sha256': pin, 'freeze_file': str(target / 'Freeze.json'), 'guest': plan['guest'], 'private_values_read': 0}


def frozen(path, pin):
    require(os.name == 'nt', 'only the Windows custodian can run guest stages')
    plan = json.loads(checked(path, pin))
    root = path.parent
    require(plan['schema'] == SCHEMA and re.fullmatch(r'[0-9a-f]{40}', plan['revision']) and list(PHASES) == plan['phases']
            and HERE == root / 'Tools' / HERE.name and root == Path(plan['guest'])
            and Path(plan['private']) == Path('C:/KitSdkCandidates') / root.name and plan['scope'] == CUT_SCOPE,
            'the guest tool, output path or revision escaped the frozen packet')
    for filename, expected in plan['files'].items():
        checked(root / filename, expected)
    row = locked_case(checked(root / 'SourceLock.json', LOCK), plan['slot'])
    require(row['case_lock_sha256'] == plan['source_slot_lock_sha256'], 'slot lock changed after freezing')
    from ctypes import c_uint, c_wchar_p, windll

    drive_type = windll.kernel32.GetDriveTypeW
    drive_type.argtypes, drive_type.restype = (c_wchar_p,), c_uint
    for location in (Path(SOURCE_ROOT), Path(plan['private']).parent):
        require(location.is_absolute() and location.resolve() == location
                and drive_type(location.anchor) == 3, 'guest private storage is redirected or not fixed')
    return root, plan, row


def code(root, plan, *, extract):
    target = Path(plan['private']) / 'Code'
    with open_tar(fileobj=BytesIO(checked(root / 'Sdk.tar', plan['files']['Sdk.tar'])), mode='r:') as archive:
        members = archive.getmembers()
        require(len({row.name.casefold() for row in members}) == len(members)
                and all((row.name == 'src' or row.name.startswith('src/')) and '\\' not in row.name
                        and '..' not in PurePosixPath(row.name).parts and (row.isdir() or row.isfile()) for row in members),
                'frozen SDK archive has duplicate or redirected entries')
        if extract:
            target.mkdir(exist_ok=False)
            archive.extractall(target, members=members, filter='data')
        else:
            expected = {row.name for row in members if row.isfile()}
            actual = {path.relative_to(target).as_posix() for path in target.rglob('*') if path.is_file()}
            require(actual == expected, 'guest SDK file inventory changed')
            for name in expected:
                path = target / name
                require(not path.is_symlink() and path.resolve() == path and path.read_bytes() == archive.extractfile(name).read(),
                        'guest SDK source changed')


def worker(private, action):
    request = json.load(sys.stdin)
    sys.path[:0] = [str(private / 'Code/src'), str(HERE.parent)]
    from convert import open_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.ThroughAll.PrepareThroughPart import PrepareThroughPart
    from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ProjectThruSrc import ProjectThruSrc
    from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.RequireThruFull import RequireThruFull
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
    from interchange.Enums.EnumGeometry import GeometryKind
    from interchange.Enums.EnumValues import ValueKind
    from interchange.Features.FeatureBody import DesignBody
    from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
    from interchange.Features.FeatureStep import FeatureStep
    from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
    from interchange.geometry.Models.Selection import SelectPathElem, Selection
    from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
    from interchange.geometry.Models.SupportPlane import SupportPlane
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.geometry.Models.VectorSpace import SpaceVector
    from interchange.Records.RecordConfig import Configuration
    from interchange.Records.RecordParameter import Parameter, ParameterValue
    from interchange.Records.RecordSource import CadSource
    from SdkNativeRoundTrips import roundtrips
    from Shape import read_shape, selected_stock

    for encoding in ('ascii', 'utf-8', 'utf-8-sig', 'utf-16-le', 'utf-16-be', 'latin-1'):
        codecs.lookup(encoding)
    for name in ('interchange.brep.Validation.BrepValidate', 'interchange.document.Behavior.DocumentIo',
                 'interchange.document.Models.DocumentProvenance',
                 'interchange.document.Validation.DocumentAssemblyValidate', 'interchange.document.Validation.DocumentFeatureValidate',
                 'interchange.document.Validation.DocumentReferenceValidate'):
        import_module(name)

    attempts = []

    def audit(event, _args):
        if event in {'open', 'os.listdir', 'os.scandir', 'os.system', 'os.exec', 'os.fork', 'os.posix_spawn', 'os.startfile'} or event.startswith(('subprocess.', 'socket.', 'ctypes.', 'winreg.')):
            attempts.append(event)
            raise PermissionError('guarded SDK attempted runtime external access: ' + event)

    sys.addaudithook(audit)
    recipe = request['recipe']
    if action == 'build':
        width, height, depth = recipe['stock_size_m']
        cx, cy = recipe['stock_center_m']
        points = tuple(PlaneVector(1000 * (cx + u * width / 2), 1000 * (cy + v * height / 2))
                       for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)))
        edge_ids = tuple(f'line/{index}' for index in range(4))
        lines = tuple(SketchEntity(key, GeometryKind.KLine, LineGeometry(points[index], points[(index + 1) % 4]))
                      for index, key in enumerate(edge_ids))
        relations = tuple(SketchRelation('axis/' + key, 'horizontal' if index % 2 == 0 else 'vertical', (ConstraintRef(key),))
                          for index, key in enumerate(edge_ids))
        frame = PrincipalFrame(recipe['axis'])
        transform = Transform(*(SpaceVector(*row) for row in (frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue)))
        plane = SupportPlane('plane/cut', {'x': 'Right Plane', 'y': 'Top Plane', 'z': 'Front Plane'}[recipe['axis']], transform)
        stock = Sketch('sketch/stock', 'StockProfile', plane.id, lines, constraints=relations, closed_profile_entity_ids=(edge_ids,))
        circle = SketchEntity('circle/cut', GeometryKind.KCircle, CircleGeometry(
            PlaneVector(*(value * 1000 for value in recipe['circle_center_m'])), recipe['radius_m'] * 1000))
        profile = Sketch('sketch/cut', 'ThroughProfile', plane.id, (circle,), closed_profile_entity_ids=((circle.id,),))
        length = ParameterValue(depth * 1000, ValueKind.KLength, 'mm')
        boss = FeatureStep('feature/stock', 'StockBoss', FeatureKind.KExtrusion, 0, sketch_id=stock.id, parameter_ids=('parameter/stock',),
                           operation=BooleanOp.KCreate, definition=ExtrudeFeature(length, ExtrudeEnd.KMidPlane, symmetric=True))
        selection = Selection('selection/stock', 'StockBoss body', (SelectPathElem('feature', boss.id, 'body'),))
        cut = FeatureStep('feature/cut', 'ThroughFeature', FeatureKind.KExtrusion, 1, (boss.id,), profile.id,
                          operation=BooleanOp.KCutOperation, selection_ids=(selection.id,), definition=ExtrudeFeature(
                              end_condition=ExtrudeEnd.KThroughAll, reversed=recipe['direction'] != 'reverse',
                              second_end_condition=ExtrudeEnd.KThroughAll if recipe['direction'] == 'both' else None))
        neutral = CadDocument(CadSource('kit-neutral', '<locked-through-all-authored-intent>', '0' * 64),
            (Configuration('configuration/default', 'Default', True),), (Parameter('parameter/stock', 'D1', length, owner_id=boss.id),),
            (plane,), (stock, profile), (selection,), (boss, cut), (DesignBody('body/cut', boss.name, cut.id),), metadata={'name': recipe['name']})
        target = BytesIO()
        candidate = PrepareThroughPart(neutral, target, recipe['epoch'], WriteOptions(
            configuration='Default', values={'final_destination': recipe['native_path']}))
        require(target.getvalue() == b'' and candidate.CutValue is not None and candidate.CutValue.DepthValue is None,
                'SDK wrote to the sink or introduced a cut depth')
        data = candidate.BytesValue
        archive = SldprtArchive.from_bytes(data)
        link, _, _, _, streams = roundtrips(archive, False)
        require(len(streams) == 10 and ReadFileKey(candidate.TopHeader.FieldsValue['f38'])[1]
                == ReadFileKey(link.ConfigValue.HeaderValue.FieldsValue['f38'])[1] == recipe['native_path'],
                'generated stream closure or exact final locator differs')
    else:
        data = b64decode(request['data'], validate=True)
        require(digest(data) == request['sha256'], 'stdin archive digest differs')
        streams = None
    document = open_document(data, source_format='solidworks.sldprt', strict=True, include_tessellation=False)
    document.assert_valid()
    actual = [value for value in document.feature_timeline if type(value.definition) is ExtrudeFeature]
    boss, cut = actual
    dependency = document.metadata['solidworks.typed_resolved_semantics']['cut_body_dependency']
    binding = 'cold_selected_stock_atom' if action == 'build' else 'saved_configuration_atom_alias'
    require(dependency['feature_scope_code'] == 1 and dependency['binding'] == binding and len(document.bodies) == 1
            and document.brep is not None and [value.name for value in actual] == ['StockBoss', 'ThroughFeature']
            and cut.definition.length is None and cut.definition.second_length is None,
            'strict selected stock, actual cut end or body owner differs')
    full_refused = None
    presentation_diagnostic = None
    if request.get('source_reference'):
        require(action == 'read', 'source evidence cannot enter the build worker')
        shape = read_shape(document)
        width, height, _ = recipe['stock_size_m']
        cx, cy = recipe['stock_center_m']
        require(close(shape['depth'], request['depth']) and shape['support_axis'] == recipe['axis']
                and shape['configuration_name'] == recipe['configuration']
                and shape['cut_reversed'] == (recipe['direction'] != 'reverse')
                and shape['second_through_all'] == (recipe['direction'] == 'both')
                and vectors_close(shape['stock']['minimum'], (cx - width / 2, cy - height / 2))
                and vectors_close(shape['stock']['maximum'], (cx + width / 2, cy + height / 2))
                and vectors_close(shape['tool']['center'], recipe['circle_center_m'])
                and close(shape['tool']['radius'], recipe['radius_m']), 'saved typed profiles, stock driver, frame or cut direction differs')
        source = ProjectThruSrc(document, recipe['name'])
        try:
            RequireThruFull(source.EnvelopeValue)
        except ValueError as error:
            require('continuous_automatic_scope_not_encoded_or_qualified' in str(error), 'complete source rejected for an unexpected reason')
            full_refused = True
        else:
            raise ValueError('complete source unexpectedly admitted')
    elif action in ('read', 'read-stock'):
        selected_stock(document, boss, cut, document.bodies[0])
        driver, = document.parameters
        require(driver.owner_id == boss.id and driver.name == 'D1' and driver.role == 'driving'
                and driver.value == boss.definition.length and str(driver.value.unit) == str(document.units) == 'mm'
                and close(driver.value.value / 1000, request['depth']) and not document.materials and not document.meshes,
                'saved candidate lost the actual stock dimension or added unsupported geometry')
        presentation_diagnostic = candidate_name_diagnostic(document)
    stock_fields = None
    if action == 'read-stock':
        link = ReadNativeLink(SldprtArchive.from_bytes(data), 0)
        stock_id = str(boss.attributes['native_object_id'])
        stock, = (node for node in link.ResolvedValue.RootsValue if str(NativeNodeId(node)) == stock_id)
        end = stock.FieldsValue['f818'].FieldsValue
        require(tuple(end[key] for key in ('f08', 'f0c', 'f10', 'f8c')) == (1, 6, 0, 0)
                and end['f20'] is None and (end['f18'] is not None),
                'native saved derivative did not preserve the explicit null stock display and active primary owner')
        stock_fields = {'active_depth_m': driver.value.value / 1000, 'secondary_display': None,
                        'result_body_count': len(document.bodies)}
    require(not attempts, 'the SDK swallowed an attempted runtime external access')
    response = {'sha256': digest(data), 'binding': binding, 'runtime_external_attempts': len(attempts),
                'complete_source_refused': full_refused, 'unresolved_presentation': presentation_diagnostic, 'streams': streams}
    if action == 'build':
        response['generated'] = b64encode(data).decode('ascii')
    if stock_fields is not None:
        response['physical_stock_fields'] = stock_fields
    return response


def candidate_name_diagnostic(document):
    if not document.diagnostics:
        return None
    diagnostic, = document.diagnostics
    prefix = 'native name records unavailable for '
    require(diagnostic.code == 'sldprt.native_record_unresolved' and diagnostic.severity == 'info'
            and diagnostic.message.startswith(prefix), 'saved candidate has an unexpected retained diagnostic')
    actual = {str(feature.attributes.get('native_object_id')): feature.name for feature in document.feature_timeline}
    owners = []
    for row in diagnostic.message[len(prefix):].split(', '):
        identity, name = row.split(':', 1)
        require(identity.isdecimal() and actual.get(identity) == name, 'saved name diagnostic has a different or stale owner')
        owners.append('Exploded Views' if name == 'Exploded Views ' + identity else name)
    require(owners == ['Ambient', 'Directional1', 'Directional2', 'Directional3', 'Exploded Views', 'Lights and Cameras'],
            'saved candidate has unmapped diagnostics beyond disclosed presentation owners')
    return {'code': diagnostic.code, 'severity': str(diagnostic.severity), 'owners': owners}


def child(private, action, request):
    run = subprocess.run([sys.executable, '-I', '-B', str(HERE), 'worker', str(private), action],
                         input=encode(request), capture_output=True, timeout=120)
    require(run.returncode == 0, 'isolated SDK worker refused: ' + run.stderr.decode(errors='replace').strip().split('\n')[-1])
    return json.loads(run.stdout)


def check_disclosed_stock(root, plan):
    packet = root.with_name(STOCK_PACKET)
    calibration = json.loads(checked(packet / 'Freeze.json', STOCK_FREEZE))
    native_root = Path('C:/KitSdkCandidates') / STOCK_PACKET
    require(calibration['private'] == str(native_root) and native_root.resolve() == native_root,
            'disclosed stock calibration path differs')
    native = json.loads(checked(native_root / 'Result.json', STOCK_NATIVE))
    require(native['passed'] and native['freeze_sha256'] == STOCK_FREEZE and len(native['phase_sha256']) == 6,
            'disclosed stock comparison is not qualified')
    saved_folder = native_root / 'Arms/Absent/Generated'
    generated = json.loads(checked(saved_folder / 'Record.json', native['phase_sha256']['Absent/Generated']))
    result = generated['result']
    require(generated['passed'] and result['save'] == [True, 0, 0]
            and result['saved']['stock']['depth_reverse_m'] == 0, 'disclosed derivative was not saved cleanly')
    data = checked(saved_folder / 'Saved.SLDPRT', result['saved_sha256'])
    case = json.loads(checked(packet / 'CandidateCase.json', calibration['files']['CandidateCase.json']))
    depth = case['prediction']['edited']['stock_depth_m']
    require(close(result['saved']['stock']['depth_forward_m'], depth), 'disclosed edited depth changed')
    private = native_root.with_name('MidPlaneStockSecondarySdk01')
    require(private.resolve() == private and not private.is_symlink(), 'disclosed SDK readback directory is redirected')
    private.mkdir(exist_ok=True)
    code(root, plan | {'private': str(private)}, extract=not (private / 'Code').exists())
    response = child(private, 'read-stock', {'recipe': case['recipe'], 'data': b64encode(data).decode(),
                                            'sha256': result['saved_sha256'], 'depth': depth})
    output = {'passed': True, 'revision': plan['revision'], 'sdk_tar_sha256': plan['files']['Sdk.tar'],
              'native_result_sha256': STOCK_NATIVE, 'saved_phase_sha256': native['phase_sha256']['Absent/Generated'],
              'readback': response, 'sealed_payloads_read': 0, 'new_native_processes': 0}
    return output | {'receipt_sha256': publish(private / 'Result.json', encode(output))}


def prepare(root, plan, frozen_pin):
    sys.path.insert(0, str(root / 'Tools'))
    from ThroughAllSourcePlan import SCHEMA as CASE_SCHEMA, geometry, validate

    spec_path = Path(SOURCE_ROOT / SOURCE_PACKET / 'D00/SealedSpecs.json')
    spec = json.loads(checked(spec_path, SPEC))
    require(spec['schema'] == CASE_SCHEMA and len(spec['cases']) == 4, 'opaque source cohort differs')
    case, = (row for row in spec['cases'] if row['id'] == plan['slot'])
    validate(case)
    require(case['operation'] == 'cut' and case['split'] == 'heldout', 'selected locked source is not an analytic cut')
    private = Path(plan['private'])
    require(not private.exists() and private.parent.resolve() == private.parent, 'guest private output root is present or redirected')
    private.mkdir(parents=True, exist_ok=False)
    code(root, plan, extract=True)
    name = 'KitThroughAll' + plan['slot']
    relative = f'GeneratedInput/{name}.SLDPRT'
    recipe = {key: case[key] for key in ('stock_size_m', 'stock_center_m', 'circle_center_m', 'radius_m', 'direction')}
    recipe.update(name=name, axis=AXES[case['plane']], configuration='Default', native_path=str(private / relative), epoch=plan['epoch'])
    predictions = {state: geometry(case, state == 'edited') | {'stock_depth_m': depth}
                   for state, depth in (('source', case['stock_size_m'][2]), ('edited', case['edit_stock_depth_m']))}
    require(all(item['analytic_qualified'] for item in predictions.values()), 'independent signed prediction is unqualified')
    try:
        built = child(private, 'build', {'recipe': recipe})
        repeated = child(private, 'build', {'recipe': recipe})
        data = b64decode(built['generated'], validate=True)
        require(built == repeated and built['runtime_external_attempts'] == 0 and digest(data) == built['sha256'],
                'the two guarded builds disagree')
    except ValueError as error:
        refusal = publish(private / 'Refused.json', encode({'freeze_sha256': frozen_pin, 'reason': str(error)}))
        return {'passed': False, 'refusal_sha256': refusal, 'source_native_reads': 0, 'generated_candidates': 0}
    built.pop('generated')
    (private / 'GeneratedInput').mkdir(exist_ok=False)
    publish(private / relative, data)
    publish(private / 'ApiMetadata.json', checked(root / 'ApiMetadata.json', DISCLOSED_METADATA))
    generation = {'freeze_sha256': frozen_pin, 'source_name': case['name'], 'generated_file': relative,
                  'candidate_sha256': built['sha256'], 'build': built, 'recipe': recipe, 'prediction': predictions,
                  'source_native_reads': 0, 'scope': CUT_SCOPE, 'whole_source_admitted': False}
    pin = publish(private / 'Generation.json', encode(generation))
    return {'passed': True, 'generation_sha256': pin, 'candidate_sha256': built['sha256'],
            'predictions_sha256': digest(encode(predictions)), 'source_native_reads': 0, 'runtime_external_attempts': 0}


def generation(root, plan, freeze_pin, pin):
    private = Path(plan['private'])
    value = json.loads(checked(private / 'Generation.json', pin))
    require(value['freeze_sha256'] == freeze_pin and value['source_native_reads'] == 0 and value['scope'] == CUT_SCOPE
            and Path(value['recipe']['native_path']) == private / value['generated_file'], 'generation did not bind original custody or encoded destination')
    checked(private / 'ApiMetadata.json', DISCLOSED_METADATA)
    control = plan['control']['location']
    job = {'control_file': control, 'generated_file': value['generated_file'], 'files_sha256': {
        control: plan['control']['sha256'], value['generated_file']: value['candidate_sha256']}}
    expected = json.loads(checked(root / 'ExpectedTree.json', plan['files']['ExpectedTree.json']))
    return private, value, job, expected


def source_reference(plan, row, value):
    original = Path(SOURCE_ROOT / SOURCE_PACKET / plan['slot'])
    source_progress = Path(SHARED_GUEST / SOURCE / 'Progress' / plan['slot'])
    locked = json.loads(checked(source_progress / 'lock/Record.json', row['case_lock_sha256']))
    require(locked['passed'] and locked['source_locked'] and locked['heldout_source_locked']
            and locked['native_artifacts'] == row['native_artifacts'], 'original source custody lock differs')
    author = json.loads(checked(original / 'SavedAuthor.json', row['source_manifest_sha256']))
    raw = {}
    for role in SOURCE_PHASES:
        spec = row['phase_records'][role]
        row_progress = json.loads(checked(source_progress / role / 'Record.json', spec['public_record_sha256']))
        require(row_progress['passed'] and row_progress['stage'] == 'passed'
                and row_progress['case_id'] == plan['slot'] and row_progress['identity'] == spec['native_identity'],
                'original frozen phase identity or health differs')
        if role not in ('before', 'after'):
            raw[role] = json.loads(checked(original / role / 'Private.json', row_progress['private_record_sha256']))
            require(raw[role]['passed'] and raw[role]['result']['passed'] and not raw[role]['result']['dialogs'],
                    'original native phase did not qualify')
    states = {}
    for state in ('source', 'edited'):
        descriptor = row['native_artifacts'][state]
        data = checked(original / 'Native' / state.title() / (value['source_name'] + '.SLDPRT'), descriptor['sha256'])
        require(author['saved_files'][state] == descriptor | {'status': [True, 0, 0]} and len(data) == descriptor['bytes']
                and raw['reopen-' + state]['result']['inputs_unchanged'], 'actual native reference save or reopen custody differs')
        states[state] = (author[state], raw['reopen-' + state]['result'], descriptor['sha256'], data)
    return states


def close(actual, expected, absolute=1e-12):
    return isclose(actual, expected, rel_tol=1e-6, abs_tol=absolute)


def vectors_close(actual, expected, absolute=1e-12):
    return all(close(a, b, absolute) for a, b in zip(actual, expected, strict=True))


def compare_state(source, candidate, depth, expected_tree, source_doc, candidate_doc):
    from Compare import differences

    require(source['bodies'] == candidate['body_count'] == 1 and candidate['configuration'] == 'Default', 'native solid or configuration differs')
    require(source['tree'] == candidate['tree'] and [[node['name'], node['type'], node['parent']] for node in source['tree']] == expected_tree,
            'unfiltered recursive feature tree differs')
    for row, name in ((source, source_doc), (candidate, candidate_doc)):
        dim, = row['stock']['dimensions']
        require(dim['name'] == f'D1@StockBoss@{name}.Part' and dim['driven_state'] == 2 and not dim['read_only']
                and close(dim['value_m'], depth) and row['operation']['dimensions'] == []
                and close(row['stock']['depth_forward_m'], depth)
                and row['operation']['depth_forward_m'] == row['operation']['depth_reverse_m'] == 0,
                'actual stock D1 or depthless cut ownership differs')
    for role in ('stock', 'operation'):
        left, right = ({key: value for key, value in state[role].items() if key != 'dimensions'} for state in (source, candidate))
        require(not differences(left, right), 'native feature parent or end definition differs')
    for name in source['profiles']:
        left, right = (row['profiles'][name]['sketch_to_model'][:13] for row in (source, candidate))
        require(not differences(left, right), 'actual sketch origin or principal frame differs')
    masses = [row['mass'] for row in (source, candidate)]
    require(all(close(value['mass'], value['volume'], 0) for value in masses)
            and all(close(masses[0][key], masses[1][key], 0) for key in ('volume', 'area', 'mass'))
            and vectors_close(masses[0]['com'], masses[1]['com'], 1e-10),
            'actual paired volume, area, centre or material-free COM mass differs')


def summarize(root, plan, row, private, value, job, tree, pin):
    from InspectSelectedThroughAll import phase_row

    phases = {name: phase_row(private, name) for name in PHASES}
    receipts = {name: digest((private / 'Inspection' / name / 'Record.json').read_bytes())
                for name in PHASES if not phases[name].get('missing_record')}
    summary = {'generation_sha256': pin, 'phase_receipt_sha256': receipts, 'passed': False,
               'whole_source_admitted': False, 'continuous_automatic_selection_qualified': False,
               'original_source_equivalence': False, 'public_writer_qualified': False, 'heldout_credit': 0}
    try:
        require(all(record['passed'] and record['result']['open'] == [True, 0, 0] and record['result']['input_immutable']
                    and record['result']['oracle_identity']['sha256'] == ORACLE
                    and record['result']['oracle_identity']['file_version'] == BUILD
                    and record['checks'] and all(check['passed'] for check in record['checks']) for record in phases.values()),
                'a candidate or healthy-control phase is missing or failed')
        ticks = {record['result']['oracle_identity']['process_creation_filetime'] for record in phases.values()}
        original_ticks = {value['native_identity']['process_creation_filetime'] for value in row['phase_records'].values()}
        require(len(ticks) == 4 and not ticks & original_ticks and all(
                before['finished_at'] <= after['started_at'] for before, after in zip(phases.values(), tuple(phases.values())[1:])),
                'candidate phases were unordered or reused a native process')
        edited = phases['Generated']['result']
        reopened = phases['Reopen']['result']
        require(edited['save'] == [True, 0, 0] and edited['saved_sha256'] == reopened['input_sha256'], 'saved candidate custody differs')
        require(all(phase['result']['rebuilt']['stock_axis_relation_types'] == [4, 4, 5, 5] for phase in phases.values()),
                'actual native stock relations differ from disclosed controls')
        checked(Path(plan['control']['location']), plan['control']['sha256'])
        checked(private / job['generated_file'], value['candidate_sha256'])
        derivative = checked(private / 'Inspection/Generated/Saved.SLDPRT', edited['saved_sha256'])
        code(root, plan, extract=False)
        sys.path.insert(0, str(private / 'Code/src'))
        refs = source_reference(plan, row, value)
        typed = {}
        for state in ('source', 'edited'):
            authored, fresh, source_sha, original = refs[state]
            depth = value['prediction'][state]['stock_depth_m']
            typed[state] = child(private, 'read', {'recipe': value['recipe'], 'data': b64encode(original).decode(),
                                                   'sha256': source_sha, 'depth': depth, 'source_reference': True})
            require(fresh['rebuilt']['prediction'] == {key: scalar for key, scalar in value['prediction'][state].items() if key != 'stock_depth_m'},
                    'original observation and frozen independent prediction inputs differ')
            observations = (edited['initial'], edited['rebuilt']) if state == 'source' else (
                edited['edited'], edited['saved'], reopened['initial'], reopened['rebuilt'])
            titles = (value['recipe']['name'],) * (2 if state == 'source' else 1) + (() if state == 'source' else ('Saved',) * 3)
            for current, title in zip(observations, titles, strict=True):
                compare_state(fresh['rebuilt'], current, depth, tree, value['source_name'], title)
                require(fresh['initial']['tree'] == authored['tree'] == fresh['rebuilt']['tree'], 'locked source native tree changed on save or reopen')
        typed['candidate_saved'] = child(private, 'read', {'recipe': value['recipe'], 'data': b64encode(derivative).decode(),
            'sha256': edited['saved_sha256'], 'depth': value['prediction']['edited']['stock_depth_m']})
        summary.update(passed=True, matched_candidate_snapshots=6, new_native_processes=4, locked_source_native_processes=5,
                       saved_selected_scope=typed, source_native_reads_after_generation=True)
    except (KeyError, ValueError, OSError) as error:
        summary['refusal'] = str(error)
    pin = publish(private / 'Comparison.json', encode(summary))
    return {'passed': summary['passed'], 'scoped_selected_stock_match': summary['passed'], 'comparison_sha256': pin,
            'new_native_processes': summary.get('new_native_processes'),
            'whole_source_admitted': False, 'heldout_credit': 0}


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest='action', required=True)
    freeze_cmd = commands.add_parser('freeze')
    freeze_cmd.add_argument('name')
    freeze_cmd.add_argument('--slot', choices=SLOTS, required=True)
    freeze_cmd.add_argument('--epoch', type=int, required=True)
    freeze_cmd.add_argument('--revision', default=REVISION)
    for mode in ('disclosed-stock', 'prepare', 'phase', 'summary'):
        cmd = commands.add_parser(mode)
        cmd.add_argument('freeze', type=Path)
        cmd.add_argument('freeze_pin')
        if mode in ('phase', 'summary'):
            cmd.add_argument('generation_pin')
        if mode == 'phase':
            cmd.add_argument('phase', choices=PHASES)
    child_cmd = commands.add_parser('worker')
    child_cmd.add_argument('private', type=Path)
    child_cmd.add_argument('worker_mode', choices=('build', 'read', 'read-stock'))
    args = parser.parse_args()
    if args.action == 'worker':
        require(os.name == 'nt', 'isolated replay belongs to the guest')
        result = worker(args.private, args.worker_mode)
    elif args.action == 'freeze':
        result = freeze(args.name, args.slot, args.epoch, args.revision)
    else:
        root, plan, row = frozen(args.freeze, args.freeze_pin)
        if args.action == 'disclosed-stock':
            result = check_disclosed_stock(root, plan)
        elif args.action == 'prepare':
            result = prepare(root, plan, args.freeze_pin)
        else:
            private, value, job, tree = generation(root, plan, args.freeze_pin, args.generation_pin)
            sys.path.insert(0, str(root / 'Tools'))
            if args.action == 'phase':
                from InspectSelectedThroughAll import phase, phase_row

                if args.phase in ('Generated', 'Reopen'):
                    require(phase_row(private, 'ControlBefore')['passed'], 'the leading disclosed control did not pass')
                control = json.loads(checked(root / 'ControlCase.json', plan['files']['ControlCase.json']))
                case = {'recipe': value['recipe'], 'prediction': value['prediction'], 'expected_tree': tree}
                result = {'passed': phase(private, job, case, control, args.phase), 'phase': args.phase}
            else:
                result = summarize(root, plan, row, private, value, job, tree, args.generation_pin)
    sys.stdout.buffer.write(encode(result))
    return int(result.get('passed') is False)


if __name__ == '__main__':
    raise SystemExit(main())
