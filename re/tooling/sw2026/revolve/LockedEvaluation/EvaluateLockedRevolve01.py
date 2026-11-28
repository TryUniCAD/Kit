from argparse import ArgumentParser
from base64 import b64decode, b64encode
import codecs
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import cos, isclose, isfinite, radians, sin, tau
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
from tarfile import open as open_tar


HERE = Path(__file__).resolve()
HOME = Path('/Users/odin')
SHARED = HOME / 'Documents/UniCAD/Oracle121Takeover'
DISCLOSED = SHARED / 'GeneratedOrdinaryRevolveNative01'
SCHEMA = 'kit.sw2026.locked-ordinary-revolve-sdk-evaluation.v1'
REVISION = '8302c824a15830b837c72db75f79cabe5693d200'
FIRST_WRITER = 'acb80309a13b8002ae8251305b2cb937da1611c5'
FIRST_PREPARATION = '608d0e8276d1834e1c45ce24e8bedaa18c5c3f6a'
LOCK_FILE = 're/solidworks/v2026/heldout/OrdinaryRevolveSourceLock.json'
LOCK = 'bf4a857b222a9ea61d5d74007fbde4090d95d1563aa8025de3b01454e1839b2f'
SPEC = '35a3af9a5195b1c723d7a2e08f370465c016923cff3e07b625cccaf08314cccc'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
BUILD = '34.5.2.0604'
CONTROL = 'Control/RevolveFull.SLDPRT'
CONTROL_PATH = PureWindowsPath(r'\\Mac\Home\Documents\UniCAD\Oracle121Takeover\GeneratedOrdinaryRevolveNative01', CONTROL)
DISCLOSED_PACKET = 'd16de9429e638f9dea4ad5e3027c98da13bfd019565746af676c37a7dd852a45'
DISCLOSED_OBSERVATION = '52833c66d1dd3f279d518217f6796f0df9338ebac565e9b5fd85d5c7a3433c51'
CONTROL_SHA = '28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0'
TOOLS = ('AuthorCurves.py', 'AuthorRevolveSources.py', 'InspectFresh.py', 'OracleIdentity.py',
         'SdkRevolveObserver01.py', 'SdkRevolveTree01.py', 'Swapp.py')
BRIDGE = 're/tooling/sw2026/revolve/Preparation/'
SLOTS = ('RevolveHeldoutFirst', 'RevolveHeldoutSecond')
PHASES = ('ControlBefore', 'OriginalEdit', 'OriginalReopen', 'CandidateEdit', 'CandidateReopen', 'ControlAfter')
CASE_KEYS = {'name', 'split', 'plane', 'radius_m', 'axial_m', 'axis_x_m', 'axis_axial_m', 'angle_deg', 'reverse', 'edit_angle_deg'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def encode(data):
    return (json.dumps(data, allow_nan=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def checked(path, wanted):
    require(path.is_file() and not path.is_symlink(), 'missing or redirected frozen file: ' + path.name)
    data = path.read_bytes()
    require(digest(data) == wanted, 'changed frozen file: ' + path.name)
    return data


def publish(path, data):
    with path.open('xb') as stream:
        stream.write(data)
    return digest(data)


def absolute(path):
    value = PureWindowsPath(path)
    require(value.is_absolute() and '..' not in value.parts and '.' not in value.parts,
            'the frozen Windows locator must be absolute and canonical')
    return value


def lock_row(lock, slot):
    require(lock['passed'] and lock['heldout_results_sealed'] and lock['writer_output_count'] == 0
            and lock['specs_sha256'] == SPEC and lock['oracle_sha256'] == ORACLE
            and lock['oracle_file_version'] == BUILD and lock['distinct_processes'] == 12
            and lock['control_before_healthy'] and lock['control_after_healthy'], 'wrong pre-writer native lock')
    rows = [row for row in lock['cases'] if row['name'] == slot and row['split'] == 'heldout']
    require(len(rows) == 1 and rows[0]['passed'] and len(rows[0]['phase_record_sha256']) == 2,
            'the pre-writer lock has no healthy exact original in this slot')
    return rows[0]


def freeze(args):
    require(os.name != 'nt' and re.fullmatch(r'SdkLockedRevolve[0-9]{2}', args.name), 'use a fresh host packet name')
    root = SHARED / args.name
    private = PureWindowsPath('C:/KitSdkCandidates', args.name)
    spec, reference = absolute(args.spec), absolute(args.reference)
    guest = PureWindowsPath(r'\\Mac\Home', *root.relative_to(HOME).parts)
    require(root.resolve() == root and not root.exists() and spec.suffix.casefold() == '.json'
            and not spec.is_relative_to(private) and not reference.is_relative_to(private), 'freeze paths overlap or already exist')
    repo = HERE.parents[5]

    def git(*argv):
        return subprocess.run(['git', '-C', str(repo), *argv], check=True, capture_output=True).stdout

    lock_data = git('show', REVISION + ':' + LOCK_FILE)
    require(digest(lock_data) == LOCK, 'tracked public source lock differs')
    lock = json.loads(lock_data)
    row = lock_row(lock, args.slot)
    epochs = {revision: int(git('show', '-s', '--format=%ct', revision))
              for revision in (FIRST_WRITER, FIRST_PREPARATION, REVISION)}
    for revision in (FIRST_WRITER, FIRST_PREPARATION):
        git('merge-base', '--is-ancestor', revision, REVISION)
    require(lock['finished_at'] < min(epochs.values()) and lock['finished_at'] < args.epoch <= 0xffffffff - 20,
            'the source hash lock must precede this writer and authoring epoch')
    disclosed = json.loads(checked(DISCLOSED / 'Packet.json', DISCLOSED_PACKET))
    pins = {item['path']: item['sha256'] for item in disclosed['files']}
    observed = json.loads(checked(DISCLOSED / 'Inspection/Inspection.json', DISCLOSED_OBSERVATION))
    require(observed['controls_healthy'] and observed['saved_edit_reopened'] and observed['distinct_processes'] == 10
            and observed['oracle_sha256'] == ORACLE, 'the disclosed SDK control cohort is not qualified')
    require(pins[CONTROL] == CONTROL_SHA, 'disclosed control provenance differs')
    checked(DISCLOSED / CONTROL, CONTROL_SHA)
    payloads = {f'Tools/{name}': checked(DISCLOSED / 'Tools' / name, pins[f'Tools/{name}']) for name in TOOLS}
    payloads.update({f'Tools/{name}': git('show', REVISION + ':' + BRIDGE + name)
                     for name in ('MakeRevolveRequest01.py', 'ReadRevolveInput01.py')})
    payloads['Tools/' + HERE.name] = HERE.read_bytes()
    payloads['PublicSourceLock.json'] = lock_data
    payloads['Sdk.tar'] = git('archive', '--format=tar', REVISION, 'src')
    candidate = private / 'Candidate' / ('Kit' + args.slot + '.SLDPRT')
    freeze_value = {'schema': SCHEMA, 'guest': str(guest), 'private': str(private), 'spec': str(spec),
                    'reference': str(reference), 'slot': args.slot, 'epoch': args.epoch, 'candidate': str(candidate),
                    'writer_revision': REVISION, 'writer_epochs': epochs, 'source_locked_at': lock['finished_at'],
                    'source_sha256': row['native_sha256'], 'disclosed_packet_sha256': DISCLOSED_PACKET,
                    'disclosed_observation_sha256': DISCLOSED_OBSERVATION, 'phases': list(PHASES),
                    'control': {'locator': str(CONTROL_PATH), 'sha256': CONTROL_SHA},
                    'files': {name: digest(data) for name, data in sorted(payloads.items())},
                    'complete_original_source_conversion': False, 'heldout_credit': 0}
    root.mkdir(mode=0o700, exist_ok=False)
    for name, data in payloads.items():
        path = root / name
        path.parent.mkdir(exist_ok=True)
        publish(path, data)
    pin = publish(root / 'Freeze.json', encode(freeze_value))
    return {'freeze_sha256': pin, 'host_packet': str(root), 'guest_freeze': str(guest / 'Freeze.json'),
            'native_candidate': str(candidate), 'private_input_reads': 0}


def read_freeze(path, pin):
    require(os.name == 'nt', 'these phases are guest-only')
    freeze_value = json.loads(checked(path, pin))
    root = path.parent
    required = {'PublicSourceLock.json', 'Sdk.tar', *(f'Tools/{name}' for name in TOOLS),
                'Tools/MakeRevolveRequest01.py', 'Tools/ReadRevolveInput01.py', 'Tools/' + HERE.name}
    require(freeze_value['schema'] == SCHEMA and freeze_value['writer_revision'] == REVISION
            and freeze_value['phases'] == list(PHASES) and path.name == 'Freeze.json'
            and root == Path(freeze_value['guest']) and HERE == root / 'Tools' / HERE.name
            and freeze_value['control'] == {'locator': str(CONTROL_PATH), 'sha256': CONTROL_SHA}
            and set(freeze_value['files']) == required, 'unexpected frozen packet or guest locator')
    for name, wanted in freeze_value['files'].items():
        checked(root / name, wanted)
    lock = lock_row(json.loads(checked(root / 'PublicSourceLock.json', LOCK)), freeze_value['slot'])
    require(lock['native_sha256'] == freeze_value['source_sha256'], 'frozen source hash differs from its original lock')
    return root, freeze_value, lock


def released_intent(spec, slot):
    require(spec['schema'] == 'kit.sw2026.ordinary-revolve-specs.v1', 'unexpected locked authored schema')
    rows = [case for case in spec['cases'] if case['name'] == slot]
    require(len(rows) == 1 and set(rows[0]) == CASE_KEYS, 'locked source intent has missing or additional owners')
    case = rows[0]
    require(case['split'] == 'heldout' and case['plane'] == 'front' and type(case['reverse']) is bool,
            'locked source is outside the canonical Front profile')
    ri, ro = case['radius_m']
    low, high = case['axial_m']
    a, b = case['axis_axial_m']
    angle, edited = map(radians, (case['angle_deg'], case['edit_angle_deg']))
    require(all(type(value) in (int, float) and isfinite(value) for value in (ri, ro, low, high, a, b, case['axis_x_m']))
            and 0 < ri < ro and a < low < high < b and b - a >= 1e-8
            and 1e-8 < angle < tau and 1e-8 < edited < tau and angle != edited, 'locked shape or driving edit is outside the measured profile')
    return case


def prediction(case, angle_degrees):
    ri, ro = case['radius_m']
    low, high = case['axial_m']
    angle = radians(angle_degrees)
    height = high - low
    delta = ro**2 - ri**2
    coefficient = 2 * (ro**3 - ri**3) / (3 * angle * delta)
    sign = 1 if case['reverse'] else -1
    volume = height * angle * delta / 2
    return {'bodies': 1, 'angle': angle, 'reverse': case['reverse'], 'signed_direction': -1,
            'volume': volume, 'area': height * angle * (ri + ro) + angle * delta + 2 * height * (ro - ri),
            'centre': [case['axis_x_m'] + coefficient * sin(angle), (high + low) / 2, sign * coefficient * (1 - cos(angle))],
            'mass': volume}


def worker(root, action):
    request = json.load(sys.stdin)
    sys.path[:0] = [str(root / 'Code/src'), str(HERE.parent)]
    from convert import open_document
    from convert.api.ApiContext import GetRegistry
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
    from interchange.Features.FeatureAngleRev import AngularRevolve
    from MakeRevolveRequest01 import make_request

    for name in ('ascii', 'utf-8', 'utf-8-sig', 'utf-16-le', 'utf-16-be', 'latin-1'):
        codecs.lookup(name)
    for name in ('interchange.brep.Validation.BrepValidate', 'interchange.document.Behavior.DocumentIo',
                 'interchange.document.Models.DocumentProvenance', 'interchange.document.Models.DocumentWalk',
                 'interchange.document.Validation.AngleRevValidate', 'interchange.document.Validation.DocumentAssemblyValidate',
                 'interchange.document.Validation.DocumentFeatureValidate', 'interchange.document.Validation.DocumentReferenceValidate',
                 'interchange.document.Validation.PlaneRevValidate', 'interchange.document.Validation.DistExtValidate'):
        import_module(name)
    GetRegistry()

    def audit(event, _arguments):
        if event.startswith(('subprocess.', 'socket.', 'ctypes.')) or event in {
            'open', 'os.listdir', 'os.scandir', 'os.system', 'os.exec', 'os.fork', 'os.posix_spawn',
        }:
            raise PermissionError('guarded SDK attempted an external operation: ' + event)

    sys.addaudithook(audit)
    if action == 'build':
        neutral, _ = make_request(request['neutral'])
        epoch, target = request['neutral']['created_at'], request['neutral']['self_path']
        options = WriteOptions(configuration='Default', values={'final_destination': target})
        sink = BytesIO()
        output = PrepareRevolve(neutral, sink, epoch, options)
        data = output.BytesValue
        require(not sink.getvalue() and output.InputValue.OutputValue.PathName == target, 'construction touched output or changed locator')
    else:
        data = b64decode(request['input'], validate=True)
        require(digest(data) == request['input_sha256'], 'stdin native bytes differ')
    expected = request['expected']
    owner, = ReadRevOwners(ReadNativeLink(SldprtArchive.from_bytes(data), 0))
    require(owner.AngleValue.NameValue == 'D1' and owner.IsReverse == expected['reverse']
            and isclose(owner.AngleValue.RadiansValue, expected['angle'], rel_tol=1e-12, abs_tol=1e-14), 'typed angle or reversal differs')
    document = open_document(data, source_format='solidworks.sldprt', strict=True, include_tessellation=False)
    document.assert_valid()
    revolutions = [row for row in document.feature_timeline if isinstance(row.definition, AngularRevolve)]
    require(document.metadata['solidworks.typed_revolve_semantics']['status'] == 'projected'
            and document.brep is not None and len(document.bodies) == len(revolutions) == 1,
            'default strict SDK read lacks complete geometry or revolve ownership')
    feature = revolutions[0]
    require(document.bodies[0].final_feature_id == feature.id and len(feature.parameter_ids) == 1
            and len(feature.selection_ids) == 1, 'public solid or angular driver is unbound')
    result = {'payload_sha256': digest(data), 'runtime_external_attempts': 0,
              'typed_angle': owner.AngleValue.RadiansValue, 'body_label': document.bodies[0].name}
    if action == 'build':
        result['payload'] = b64encode(data).decode()
    sys.stdout.buffer.write(encode(result))


def child(private, action, request):
    result = subprocess.run([sys.executable, '-I', '-S', '-B', str(HERE), 'worker', str(private), action], input=encode(request),
                            capture_output=True, check=False)
    if result.returncode:
        lines = result.stderr.decode(errors='replace').splitlines()
        raise ValueError('guarded SDK process failed: ' + (lines[-1] if lines else str(result.returncode)))
    return json.loads(result.stdout)


def sdk_code(root, private, freeze_value, *, extract):
    target = private / 'Code'
    if extract:
        target.mkdir(exist_ok=False)
    data = checked(root / 'Sdk.tar', freeze_value['files']['Sdk.tar'])
    with open_tar(fileobj=BytesIO(data), mode='r:') as archive:
        rows = archive.getmembers()
        names = [row.name.replace('\\', '/') for row in rows]
        require(len({name.casefold() for name in names}) == len(rows)
                and all((name == 'src' or name.startswith('src/')) and '..' not in PureWindowsPath(name).parts
                        and '\\' not in row.name and (row.isfile() or row.isdir()) for name, row in zip(names, rows, strict=True)),
                'frozen SDK inventory contains redirected, duplicate or unrelated paths')
        if extract:
            archive.extractall(target, members=rows, filter='data')
        else:
            files = {path.relative_to(target).as_posix(): path for path in target.rglob('*') if path.is_file()}
            require(set(files) == {row.name for row in rows if row.isfile()}, 'frozen guest SDK file inventory changed')
            for row in rows:
                if row.isfile():
                    path = files[row.name]
                    require(path.resolve() == path and not path.is_symlink()
                            and path.read_bytes() == archive.extractfile(row).read(), 'guest SDK file changed')


def prepare(root, freeze_value, pin):
    private = Path(freeze_value['private'])
    require(not private.exists() and private.parent.resolve() == private.parent, 'guest output root is present or redirected')
    try:
        source_spec = json.loads(checked(Path(freeze_value['spec']), SPEC))
        case = released_intent(source_spec, freeze_value['slot'])
    except (KeyError, TypeError, ValueError) as error:
        return {'eligible': False, 'reason': str(error), 'generation_credit': 0, 'native_processes': 0,
                'original_files_read': 0, 'complete_original_source_conversion': False, 'heldout_credit': 0}

    name = 'Kit' + case['name']
    candidate = Path(freeze_value['candidate'])
    require(candidate == private / 'Candidate' / (name + '.SLDPRT'), 'candidate lost its encoded guest self locator')
    expected = {'initial': prediction(case, case['angle_deg']), 'edited': prediction(case, case['edit_angle_deg'])}
    target = {'name': name, 'radial_mm': [value * 1000 for value in case['radius_m']],
              'axial_mm': [value * 1000 for value in case['axial_m']], 'axis_x_mm': case['axis_x_m'] * 1000,
              'axis_span_mm': [value * 1000 for value in case['axis_axial_m']], 'angle_deg': case['angle_deg'],
              'reverse': case['reverse'], 'edit_angle_deg': case['edit_angle_deg'], 'created_at': freeze_value['epoch'],
              'self_path': str(candidate)}
    private.mkdir(parents=True, exist_ok=False)
    sdk_code(root, private, freeze_value, extract=True)
    build_request = {'neutral': target, 'expected': expected['initial']}
    try:
        generated = child(private, 'build', build_request)
    except ValueError as error:
        refusal = publish(private / 'PreparationRefused.json', encode({'freeze_sha256': pin, 'reason': str(error)}))
        return {'eligible': False, 'reason': 'guarded SDK preparation refused', 'refusal_sha256': refusal,
                'generation_credit': 0, 'native_processes': 0,
                'original_files_read': 0, 'complete_original_source_conversion': False, 'heldout_credit': 0}
    data = b64decode(generated.pop('payload'), validate=True)
    require(generated['runtime_external_attempts'] == 0 and digest(data) == generated['payload_sha256'],
            'guarded neutral construction did not prove exact output or zero reads')
    for dirname in ('Candidate', 'Edited/Original', 'Edited/Candidate', 'Observations'):
        (private / dirname).mkdir(parents=True, exist_ok=False)
    candidate_pin = publish(candidate, data)
    evidence = {'freeze_sha256': pin, 'case': case, 'expected': expected, 'candidate_sha256': candidate_pin,
                'neutral_request_sha256': digest(encode(build_request)), 'build': generated, 'original_files_read': 0,
                'complete_original_source_conversion': False, 'heldout_credit': 0}
    generation_pin = publish(private / 'Generation.json', encode(evidence))
    return {'eligible': True, 'generation_sha256': generation_pin, 'candidate_sha256': candidate_pin,
            'prediction_sha256': digest(encode(expected)), 'runtime_external_attempts': 0, 'original_files_read': 0,
            'complete_original_source_conversion': False, 'heldout_credit': 0}


def measure(row, expected):
    def close(actual, wanted, absolute=0):
        return isclose(actual, wanted, rel_tol=2e-7, abs_tol=absolute)

    require(row['bodies'] == expected['bodies'] and row['forward_handedness'] == expected['signed_direction']
            and row['reverse'] == expected['reverse'] and close(row['angle_radians'], expected['angle']),
            'body, selection sense or angular value differs')
    mass = row['mass']
    require(all(close(mass[key], expected[key]) for key in ('mass', 'volume', 'area'))
            and all(close(value, wanted, 1e-10) for value, wanted in zip(mass['com'], expected['centre'], strict=True)),
            'native mass, volume, area or signed centre differs')


def native(root, freeze_value, lock, pin, generation_pin, role):
    private = Path(freeze_value['private'])
    generation = json.loads(checked(private / 'Generation.json', generation_pin))
    candidate = Path(freeze_value['candidate'])
    require(generation['freeze_sha256'] == pin and generation['case']['name'] == freeze_value['slot'], 'generation receipt differs')
    if role != 'ControlAfter':
        checked(candidate, generation['candidate_sha256'])
    phase_path = private / 'Observations' / (role + '.json')
    require(not phase_path.exists(), 'phase receipt already exists')
    index = PHASES.index(role)
    if index not in (0, len(PHASES) - 1):
        for previous in PHASES[:index]:
            item = json.loads((private / 'Observations' / (previous + '.json')).read_bytes())
            require(item['freeze_sha256'] == pin and item['generation_sha256'] == generation_pin and item['passed'],
                    'a preceding candidate phase has not passed')

    sys.path.insert(0, str(root / 'Tools'))
    import AuthorRevolveSources as sources
    from InspectFresh import healthy, inspect
    from SdkRevolveObserver01 import SdkRevolveObserver
    from SdkRevolveTree01 import predict_tree
    import Swapp

    result = {'freeze_sha256': pin, 'generation_sha256': generation_pin, 'role': role, 'passed': False}
    try:
        if role.startswith('Control'):
            control = Path(freeze_value['control']['locator'])
            control_sha = freeze_value['control']['sha256']
            checked(control, control_sha)
            observed = inspect(control)
            result['native_record_sha256'] = publish(private / 'Observations' / (role + '.Native.json'), encode(observed))
            require(healthy(observed) and observed['sha256'] == control_sha, 'disclosed control failed')
            checked(control, control_sha)
        else:
            case = generation['case']
            name = case['name']
            source_dir = Path(freeze_value['reference']) / 'heldout' / name
            original = source_dir / (name + '.SLDPRT')
            source_data = checked(original, lock['native_sha256'])
            require(len(source_data) == lock['native_bytes'], 'original source length differs from its public lock')
            for origin, wanted in zip(('author', 'reopen'), lock['phase_record_sha256'], strict=True):
                checked(source_dir / (name + '.' + origin + '.json'), wanted)
            is_original = role.startswith('Original')
            group = 'Original' if is_original else 'Candidate'
            source = original if is_original else candidate
            reading = role.endswith('Reopen')
            edited_path = private / 'Edited' / group / source.name
            input_data = source_data if is_original else checked(candidate, generation['candidate_sha256'])
            if reading:
                prior = json.loads((private / 'Observations' / (group + 'Edit.json')).read_bytes())
                source = edited_path
                input_data = checked(source, prior['derivative_sha256'])
            target_case = case | {'name': source.stem}
            if reading:
                target_case = target_case | {'angle_deg': target_case['edit_angle_deg']}
            expected = generation['expected']
            sdk_code(root, private, freeze_value, extract=False)
            kit = child(private, 'read', {'input': b64encode(input_data).decode(), 'input_sha256': digest(input_data),
                                         'expected': expected['edited' if reading else 'initial']})
            native_path = private / 'Observations' / (role + '.Native.json')
            require(not native_path.exists(), 'native phase record already exists')
            original_controller = Swapp.Sw

            class ReadOnlyController(original_controller):
                def open(self, path, doctype=None, *, read_only=False):
                    return super().open(path, doctype, read_only=True)

            class BoundObserver(SdkRevolveObserver):
                expected_trees = {target_case['name']: predict_tree(target_case)}

                def snapshot(self, current, label, angle_degrees):
                    require(os.path.samefile(self.get(self.model, 'GetPathName'), source)
                            and self.get(self.model, 'IsOpenedReadOnly'), 'opened wrong file or admitted a writable original')
                    preference = self.display_dimension_preference()
                    previous = bool(self.get(self.model, 'GetUserPreferenceToggle', preference))
                    if not previous:
                        self.get(self.model, 'SetUserPreferenceToggle', preference, True)
                    try:
                        boss = super().snapshot(current, label, angle_degrees)
                    finally:
                        if not previous:
                            self.get(self.model, 'SetUserPreferenceToggle', preference, False)
                        require(bool(self.get(self.model, 'GetUserPreferenceToggle', preference)) == previous,
                                'dimension display preference was not restored')
                    row = self.rec.data[label]
                    target = expected['edited' if reading or label == 'edited' else 'initial']
                    measure(row, target)
                    front = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
                    require(all(isclose(actual, wanted, rel_tol=1e-12, abs_tol=1e-12)
                                for values, targets in zip(row['profile']['frame_points'], front, strict=True)
                                for actual, wanted in zip(values, targets, strict=True)), 'native Front frame or origin differs')
                    dimensions = [dim for feature in row['features'] if feature['type'] == 'Revolution'
                                  for dim in feature.get('dims', ())]
                    require(len(dimensions) == 1 and dimensions[0].get('name') == f'D1@OrdinaryBossRevolve@{source.stem}.Part'
                            and isclose(dimensions[0]['value'], target['angle'], rel_tol=1e-12, abs_tol=1e-14),
                            'actual feature-owned D1 is missing, ambiguous or changed')
                    bodies = tuple(self.get(self.model, 'GetBodies2', 0, False) or ())
                    require(len(bodies) == 1 and isinstance(name := self.get(bodies[0], 'Name'), str) and name,
                            'actual native solid owner label is unavailable')
                    if is_original or reading:
                        require(name == kit['body_label'], 'saved native solid label differs from strict SDK read')
                    row['body_name'] = name
                    self.rec.flush()
                    return boss

            previous_author = sources.RevolveAuthor
            try:
                Swapp.sweep()
                Swapp.Sw = ReadOnlyController
                sources.RevolveAuthor = BoundObserver
                observed, native_pin = sources.run_phase(target_case, 'edited-reopen' if reading else 'reopen',
                    source, ORACLE, digest(input_data), inspect_before_rebuild=True, inspect_profile=True,
                    record_path=native_path, save_edited=None if reading else edited_path)
            finally:
                Swapp.Sw, sources.RevolveAuthor = original_controller, previous_author
            result['native_record_sha256'] = native_pin
            require(observed['passed'] and not observed['cleanup_errors'] and observed['source_immutable']
                    and observed['before_explicit_rebuild']['needs_rebuild'] == observed['before_explicit_rebuild']['whats_wrong'] == 0,
                    'native lifecycle, initial rebuild status or custody failed')
            if not reading:
                derivative = observed['edited_derivative']
                require(observed['edit']['passed'] and observed['edit']['setter_status'] == 0
                        and observed['display_dimension_preference']['restored'] and derivative['save_status'] == [True, 0, 0],
                        'actual driving edit, preference restoration or native save failed')
                checked(edited_path, derivative['sha256'])
                result['derivative_sha256'] = derivative['sha256']
            checked(original, lock['native_sha256'])
            checked(candidate, generation['candidate_sha256'])
            result.update(sdk_read=kit, source_sha256=digest(input_data))
        identity = observed['oracle_identity']
        require(identity['version_matches'] and identity['sha256'] == ORACLE and identity['file_version'] == BUILD,
                'phase used a different installed oracle')
        result.update(passed=True, oracle_process=identity['process_creation_filetime'])
    except Exception as error:
        result['refusal'] = str(error)
    record_pin = publish(phase_path, encode(result))
    return {'phase': role, 'passed': result['passed'], 'receipt_sha256': record_pin,
            'complete_original_source_conversion': False, 'heldout_credit': 0}


def summarize(freeze_value, pin, generation_pin):
    private = Path(freeze_value['private'])
    checked(private / 'Generation.json', generation_pin)
    records = private / 'Observations'
    found = {}
    native = {}
    for role in PHASES:
        path = records / (role + '.json')
        if path.is_file():
            data = path.read_bytes()
            result = json.loads(data)
            require(result['role'] == role and result['freeze_sha256'] == pin
                    and result['generation_sha256'] == generation_pin, 'phase receipt escaped its frozen packet')
            if 'native_record_sha256' in result:
                native[role] = json.loads(checked(records / (role + '.Native.json'), result['native_record_sha256']))
            found[role] = result, digest(data)
    positive = [item for item, _ in found.values() if item['passed']]
    processes = {item['oracle_process'] for item in positive}
    passed = len(positive) == len(processes) == len(PHASES)
    comparisons, comparison_refusal = [], None
    if passed:
        try:
            for phase, label in (('Edit', 'reopened'), ('Edit', 'edited'), ('Reopen', 'reopened')):
                source, candidate = (native[group + phase][label] for group in ('Original', 'Candidate'))
                expected = {'bodies': source['bodies'], 'signed_direction': source['forward_handedness'],
                            'reverse': source['reverse'], 'angle': source['angle_radians'], 'centre': source['mass']['com']}
                expected.update({key: source['mass'][key] for key in ('mass', 'volume', 'area')})
                measure(candidate, expected)
                require(source['complete_tree'] == candidate['complete_tree'] and source['body_name'] == candidate['body_name'],
                        'source and candidate recursive native tree or actual body label differs')
                comparisons.append((phase, label))
        except (KeyError, ValueError) as error:
            comparison_refusal = str(error)
            passed = False
    return {'scoped_neutral_native_comparison_passed': passed, 'distinct_processes': len(processes),
            'source_candidate_comparisons': comparisons,
            'comparison_refusal': comparison_refusal,
            'phase_receipt_sha256': {role: value[1] for role, value in found.items()},
            'controls_healthy': all(role in found and found[role][0]['passed'] for role in ('ControlBefore', 'ControlAfter')),
            'whole_source_admission': 'refused pending complete source presentation and provenance ownership',
            'complete_original_source_conversion': False, 'heldout_credit': 0, 'public_writer_qualified': False}


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest='action', required=True)
    freeze_cmd = commands.add_parser('freeze')
    freeze_cmd.add_argument('name')
    freeze_cmd.add_argument('--slot', choices=SLOTS, required=True)
    freeze_cmd.add_argument('--spec', required=True)
    freeze_cmd.add_argument('--reference', required=True)
    freeze_cmd.add_argument('--epoch', type=int, required=True)
    for action in ('prepare', 'phase', 'summary'):
        stage = commands.add_parser(action)
        stage.add_argument('freeze', type=Path)
        stage.add_argument('pin')
        if action != 'prepare':
            stage.add_argument('generation_pin')
        if action == 'phase':
            stage.add_argument('role', choices=PHASES)
    run = commands.add_parser('worker', help='internal isolated stdin-only SDK process')
    run.add_argument('private', type=Path)
    run.add_argument('worker_action', choices=('build', 'read'))
    args = parser.parse_args()
    if args.action == 'worker':
        require(os.name == 'nt', 'this guarded SDK child is guest-only')
        worker(args.private, args.worker_action)
        return 0
    if args.action == 'freeze':
        result = freeze(args)
    else:
        root, state, lock = read_freeze(args.freeze, args.pin)
        if args.action == 'prepare':
            result = prepare(root, state, args.pin)
        elif args.action == 'phase':
            result = native(root, state, lock, args.pin, args.generation_pin, args.role)
        else:
            result = summarize(state, args.pin, args.generation_pin)
    sys.stdout.buffer.write(encode(result))
    return int(result.get('passed', result.get('eligible', result.get('scoped_neutral_native_comparison_passed', True))) is not True)


if __name__ == '__main__':
    raise SystemExit(main())
