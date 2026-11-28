from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys


HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
HOME = Path('/Users/odin')
WORKSPACE = HOME / 'Documents/UniCAD/Oracle121Takeover'
SOURCE = WORKSPACE / 'EquationSourceProtocol01/NativePacket01'
DISCLOSED = WORKSPACE / 'WidthDepthSameLocator02'
PROTOCOL = '83790d7f1bf268d310f14dfdecbfc269ba804fdcaf02b3df5fadf5f6e93567a2'
LOCK = '20b392ca5b7640570401f2fb68c25190f1449f4f688d315a16576f9921892031'
SEAL = 'de934e265d365692b37f48ed803a2dc60794c67f08c011048fddca98fb096e03'
LOCK_AT = 1795115958.4314606
SOURCE_REV = '47752a27c23ba36f6725a8dc43ef951918e42198'
FIRST_CODEC = '390ad72916d36c00d64552707968162c8b3d95ff'
FIRST_WRITER = '245258a0afdca69e52e2efbe25fe1daea671a909'
WRITER_REV = '1b70d67b854814cb5066f44028439c43f2b4a632'
DISCLOSED_TRIAL = 'da6021c5bcd50e3da7649c3c8b41d58c3ba7685d61284ca4e3b8dd1dc5478f8b'
DISCLOSED_RESULT = '1bc515ac5352d148bb5d53a3a6865a6bf247458691f420e152ccf0785a8edd84'
DISCLOSED_NEUTRAL = '2e0a84ca6f061d9c34622ba98a8a440a8322cf55ec8cc2d72b720da0b223c94f'
CONTROL = 'DisclosedEquationControl.SLDPRT'
CONTROL_SHA = '8d79922604aba1816348ae2b62d3601c44a088dccf4b1373dd17ca0e39b02e58'
METADATA = '60db6487419215724e9f48f7f17ae1f5aa373e6cb39a868dda02c31658f7f78c'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
ORACLE_VERSION = '34.5.2.0604'
SCHEMA = 'kit.sw2026.locked-width-depth-evaluation.v1'
SLOT = 'Slot02'
NAMES = ('D1@AnchorSketch', 'D2@AnchorSketch', 'D1@AnchorBoss')
EXPRESSION = '"D1@AnchorBoss" = "D1@AnchorSketch" / 2'
PHASES = ('ControlBefore', 'ReferenceEdit', 'ReferenceReopen', 'ControlAfter')
SOURCE_PHASES = ('ControlBefore', 'Author', 'ReopenOriginal', 'ReopenEdited', 'ControlAfter')
TOOLS = ('AuthorCurves.py', 'AuthorEquationSources01.py', 'AuthorRectangleAnchors.py', 'InspectCornerPointOwners.py',
         'InspectFresh.py', 'InspectSdkBlindPart.py', 'InspectSdkCornerOwners.py', 'ObserveWidthDepthPart.py',
         'OracleIdentity.py', 'PrepareWidthDepthSameLocator.py', 'SdkCornerOwnerGraph.py', 'Swapp.py')
RESEARCH = 're/tooling/sw2026'
CODE_FILES = (f'{RESEARCH}/SdkBlindPartSettings.py', f'{RESEARCH}/SdkRectDimRejects.py',
              f'{RESEARCH}/equations/BuildWidthDepthPart.py', f'{RESEARCH}/equations/ReplayPartEquationConfig.py',
              'tests/__init__.py', 'tests/Convert/__init__.py', 'tests/Convert/Solidworks/__init__.py',
              'tests/Convert/Solidworks/Research/ConstructionGuard.py')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def checked(path, wanted):
    require(path.is_file() and not path.is_symlink(), 'required frozen artifact is absent or redirected: ' + path.name)
    data = path.read_bytes()
    require(digest(data) == wanted, 'frozen artifact changed: ' + path.name)
    return data


def publish(path, payload):
    with path.open('xb') as stream:
        stream.write(payload)
    return digest(payload)


def unc(path):
    return str(PureWindowsPath(r'\\Mac\Home', *path.relative_to(HOME).parts))


def locations(name):
    require(re.fullmatch(r'WidthDepthLockedEvaluation[0-9]{2}', name), 'use an unused WidthDepthLockedEvaluationNN packet')
    return PureWindowsPath('C:/', name), PureWindowsPath(r'C:\KitSdkCandidates', name + '.SLDPRT')


def chronology(lock, binding):
    checks = ((FIRST_CODEC, 1795117723), (FIRST_WRITER, 1795121024))
    require(lock['locked_at'] == LOCK_AT and binding['source_publication'] == [SOURCE_REV, 1795116475]
            and binding['writer_sources'] == [[revision, epoch, epoch] for revision, epoch in checks]
            and LOCK_AT < binding['source_publication'][1] < min(epoch for _, epoch in checks),
            'the slot was not hash-locked and published before the applicable writer source')


def source_lock(protocol, lock, seal):
    require(protocol['guest_private_root'] == r'C:\KitEquationSource121'
            and protocol['oracle_sha256'] == ORACLE and protocol['writer_output_count'] == 0
            and protocol['api_metadata_sha256'] == METADATA and protocol['slots'][SLOT] == 'sealed_width_depth',
            'the original equation source protocol is required')
    require(lock['slot'] == seal['slot'] == SLOT and lock['source_locked'] and lock['heldout_source_locked'] and seal['sealed']
            and lock['protocol_sha256'] == seal['protocol_sha256'] == PROTOCOL
            and seal['created_at'] < lock['locked_at'] == LOCK_AT
            and lock['intent_sha256'] == seal['intent_sha256'] and lock['prediction_sha256'] == seal['prediction_sha256']
            and lock['controls_healthy'] and lock['distinct_native_processes'] == 5
            and lock['writer_output_count'] == seal['writer_output_count'] == 0
            and not lock['generated_writer_qualified'] and set(lock['phases']) == set(SOURCE_PHASES)
            and set(lock['source_files']) == {'Original', 'Edited'}, 'the original pre-writer source lock is required')
    require(all(entry['passed'] and entry['oracle_identity']['sha256'] == ORACLE for entry in lock['phases'].values())
            and len({entry['oracle_identity']['process_creation_filetime'] for entry in lock['phases'].values()}) == 5
            and all(entry['save_status'] == [True, 0, 0] for entry in lock['source_files'].values()),
            'the original source controls or phases lack exact native qualification')


def prepare(name, creation_epoch):
    import subprocess
    from zipfile import ZipFile

    private, target = locations(name)
    root = WORKSPACE / name
    require(root.resolve() == root and not root.exists() and LOCK_AT < creation_epoch <= 0xffffffff - 20,
            'use a fresh managed packet and an explicit target creation epoch')

    def git(*args):
        return subprocess.check_output(['git', *args], cwd=REPO)

    for parent, child in ((SOURCE_REV, FIRST_CODEC), (FIRST_CODEC, FIRST_WRITER), (FIRST_WRITER, WRITER_REV)):
        subprocess.run(['git', 'merge-base', '--is-ancestor', parent, child], cwd=REPO, check=True)
    protocol = checked(SOURCE / 'Protocol.json', PROTOCOL)
    lock = checked(SOURCE / 'Progress/Slot02/Lock/Record.json', LOCK)
    seal = checked(SOURCE / 'Progress/Slot02/IntentSeal/Record.json', SEAL)
    source_lock(*(json.loads(value) for value in (protocol, lock, seal)))
    archived = json.loads(git('show', SOURCE_REV + ':re/solidworks/measurements/2026/NativeEquationWidthDepthSource01.json'))
    slot = archived['width_depth_source_locks'][SLOT]
    require(slot['lock_sha256'] == LOCK and slot['locked_at'] == LOCK_AT and archived['generated_writer_outputs'] == 0,
            'the source-publication Git object does not contain the exact lock')
    binding = {'source_publication': [SOURCE_REV, int(git('show', '-s', '--format=%ct', SOURCE_REV))],
               'writer_sources': [[rev, *map(int, git('show', '-s', '--format=%at %ct', rev).split())]
                                  for rev in (FIRST_CODEC, FIRST_WRITER)]}
    chronology(json.loads(lock), binding)
    previous, native = (json.loads(checked(DISCLOSED / file, wanted)) for file, wanted in
                        (('Trial.json', DISCLOSED_TRIAL), ('Result.json', DISCLOSED_RESULT)))
    require(native['passed'] and native['controls_healthy'] and native['trial_sha256'] == DISCLOSED_TRIAL
            and native['distinct_native_processes'] == 6 and previous['revision'] == WRITER_REV
            and previous['files_sha256'][CONTROL] == CONTROL_SHA, 'the accepted disclosed reference lane is required')
    authored = json.loads(checked(DISCLOSED / 'Neutral.json', DISCLOSED_NEUTRAL))['settings']
    require(authored['density_kg_m3'] == 1 and authored['document_units']['length_unit'] == 'mm',
            'the independently authored target settings left their qualified profile')
    authored['output'] = {'path_name': str(target), 'saved_at': creation_epoch + 20}
    authored['system']['created_at'] = creation_epoch
    for folder in authored['system']['folders']:
        if folder[0] == 'moEnvFolder_c':
            folder[1] = 'Lights and Cameras'
    authored['provenance'].update(created_at=creation_epoch, modified_at=creation_epoch + 10, updated_at=creation_epoch + 10,
                                  comment='independently authored local equation part')
    closure = io.BytesIO(git('archive', '--format=zip', WRITER_REV, 'src'))
    with ZipFile(closure, 'a') as package:
        for file in CODE_FILES:
            package.writestr(file, git('show', WRITER_REV + ':' + file))
        manifest_sha = digest(canonical({file: digest(package.read(file)) for file in package.namelist() if not file.endswith('/')}))
    inputs = {'Protocol.json': protocol, 'SourceLock.json': lock, 'IntentSeal.json': seal, 'Writer.zip': closure.getvalue(),
              'TargetSettings.json': canonical(authored), 'ApiMetadata01.json': checked(SOURCE / 'ApiMetadata01.json', METADATA),
              CONTROL: checked(DISCLOSED / CONTROL, CONTROL_SHA), f'Tools/{HERE.name}': HERE.read_bytes()}
    inputs.update({f'Tools/{tool}': checked(DISCLOSED / 'Tools' / tool, previous['files_sha256'][f'Tools/{tool}']) for tool in TOOLS})
    root.mkdir(mode=0o700)
    (root / 'Tools').mkdir()
    hashes = {name: publish(root / name, data) for name, data in inputs.items()}
    job = {'schema': SCHEMA, 'oracle_sha256': ORACLE, 'writer_revision': WRITER_REV, 'chronology': binding,
           'runtime': previous['guest_runtime'], 'packet_guest_path': unc(root), 'private_output': str(private),
           'target': str(target), 'creation_epoch': creation_epoch, 'files': hashes, 'control': previous['control'],
           'code_manifest_sha256': manifest_sha, 'disclosed_native_result_sha256': DISCLOSED_RESULT, 'sealed_payloads_read_on_host': 0}
    pin = publish(root / 'Trial.json', canonical(job))
    commands = {'Verify': ['verify'], 'Generate': ['generate'], 'Attach': ['attach'],
                **{phase: ['observe', phase] for phase in PHASES}, 'Summary': ['summary']}
    prefix = ['prlctl', 'exec', 'Windows 11', '--current-user', job['runtime']['executable'], '-B', unc(root / 'Tools' / HERE.name)]
    generation = ['--generation-sha256', 'GENERATED_RECEIPT_SHA256']
    comparison = ['--comparison-sha256', 'ATTACHED_RECEIPT_SHA256']

    def prerequisites(step):
        if step in ('Verify', 'Generate'):
            return []
        return generation if step == 'Attach' else generation + comparison

    recipe = publish(root / 'Recipe.json', canonical({'trial_sha256': pin, 'ordered_steps': list(commands),
        'argv': {key: [*prefix, *command, unc(root / 'Trial.json'), pin, *prerequisites(key)] for key, command in commands.items()},
        'argv_digest_bindings': {'GENERATED_RECEIPT_SHA256': ['Generate', 'generation_sha256'],
                                 'ATTACHED_RECEIPT_SHA256': ['Attach', 'comparison_sha256']},
        'maximum_native_launches': 4, 'trailing_control_after_native_failure_if_idle': True,
        'stop_dependent_steps_after_failure': True,
        'host_wait_limit_seconds': dict(zip(commands, (60, 90, 90, 150, 240, 180, 150, 45), strict=True))}))
    print(json.dumps({'packet': str(root), 'trial_sha256': pin, 'recipe_sha256': recipe, 'frozen_inputs': len(hashes),
                      'writer_archive_sha256': hashes['Writer.zip'], 'sealed_payloads_read_on_host': 0, 'native_launches': 0}, sort_keys=True))


def read_trial(path, pin):
    import AuthorEquationSources01 as protocol_tools

    root = path.resolve(strict=True).parent
    job = json.loads(checked(path, pin))
    private, exact = locations(root.name)
    require(job['schema'] == SCHEMA and job['oracle_sha256'] == ORACLE and job['writer_revision'] == WRITER_REV
            and HERE.parent == root / 'Tools' and Path(job['packet_guest_path']).resolve() == root
            and path.name == 'Trial.json' and job['private_output'] == str(private) and job['target'] == str(exact)
            and job['files']['Protocol.json'] == PROTOCOL and job['files']['SourceLock.json'] == LOCK
            and job['files']['IntentSeal.json'] == SEAL and job['files'][CONTROL] == CONTROL_SHA
            and job['files']['ApiMetadata01.json'] == METADATA and job['sealed_payloads_read_on_host'] == 0,
            'the frozen held-out evaluation packet differs')
    require(set(job['files']) == {'Protocol.json', 'SourceLock.json', 'IntentSeal.json', 'Writer.zip', 'TargetSettings.json',
                                'ApiMetadata01.json', CONTROL, f'Tools/{HERE.name}', *(f'Tools/{name}' for name in TOOLS)},
            'the frozen evaluator file inventory differs')
    for name, wanted in job['files'].items():
        candidate = root / name
        require(candidate.resolve() == candidate and candidate.is_relative_to(root), 'the packet path is redirected')
        checked(candidate, wanted)
    protocol_tools.guest_only({'guest_runtime': job['runtime']})
    values = tuple(json.loads((root / name).read_bytes()) for name in ('Protocol.json', 'SourceLock.json', 'IntentSeal.json'))
    source_lock(*values)
    chronology(values[1], job['chronology'])
    return root, Path(private), Path(exact), job, values[1]


def verify(root, private, exact, job, pin):
    from stat import S_ISLNK
    from zipfile import ZipFile

    require(not private.exists() and private.resolve() == private and not exact.exists() and exact.resolve() == exact,
            'guest private and encoded candidate paths must be unused and unredirected')
    private.mkdir()
    code = private / 'CodeRoot'
    code.mkdir()
    (private / 'Inspection').mkdir()
    with ZipFile(root / 'Writer.zip') as archive:
        names = archive.namelist()
        require(len(set(names)) == len(names), 'writer package duplicates path names')
        for item in archive.infolist():
            member = Path(item.filename)
            require(not member.is_absolute() and '..' not in member.parts and not S_ISLNK(item.external_attr >> 16)
                    and ((code / member).resolve().is_relative_to(code)), 'unsafe writer package path')
        archive.extractall(code)
        manifest = {name: digest(archive.read(name)) for name in names if not name.endswith('/')}
    require(digest(canonical(manifest)) == job['code_manifest_sha256'], 'extracted writer manifest differs from the host pin')
    (private / 'ApiMetadata01.json').write_bytes(checked(root / 'ApiMetadata01.json', METADATA))
    (private / CONTROL).write_bytes(checked(root / CONTROL, CONTROL_SHA))
    publish(private / 'Verified.json', canonical({'trial_sha256': pin, 'source_lock_sha256': LOCK,
               'writer_archive_sha256': job['files']['Writer.zip'], 'code_manifest': manifest, 'private_slot_payloads_read': 0}))
    return {'verified': True, 'writer_code_files': len(manifest), 'native_launches': 0}


def code_root(private, pin, job):
    receipt = json.loads((private / 'Verified.json').read_bytes())
    require(receipt['trial_sha256'] == pin and receipt['writer_archive_sha256'] == job['files']['Writer.zip']
            and receipt['source_lock_sha256'] == LOCK, 'guest setup has the wrong custody')
    code = private / 'CodeRoot'
    manifest = receipt['code_manifest']
    require(digest(canonical(manifest)) == job['code_manifest_sha256']
            and set(manifest) == {path.relative_to(code).as_posix() for path in code.rglob('*') if path.is_file()},
            'extracted writer code inventory differs')
    for file, wanted in manifest.items():
        checked(code / file, wanted)
    return code


def request(intent, settings):
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeBoxProfile import MakeBoxProfile
    from interchange import CadDocument, CadSource, Configuration, DesignBody, FeatureStep, SupportPlane
    from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
    from interchange.Enums.EnumValues import ValueKind
    from interchange.Features.FeatureExtrude import ExtrudeFeature
    from interchange.Records.RecordParameter import Parameter, ParameterValue
    from interchange.geometry.Models.Transform import Transform
    from interchange.serialization.EncodeData import ToData

    require(set(intent) == {'width_mm', 'height_mm', 'depth_mm', 'divisor'} and type(intent['divisor']) is int
            and intent['divisor'] == 2 and intent['depth_mm'] == intent['width_mm'] / 2,
            'the isolated request builder admits only original geometry and one width-over-two dependency')
    width, height, depth = (intent[key] for key in ('width_mm', 'height_mm', 'depth_mm'))
    require(22.001 <= width <= 60.999 and 10.001 <= height <= 28.999, 'held-out original geometry is outside its preregistered shape')
    ids = ('parameter/width', 'parameter/height', 'parameter/depth')
    plane = SupportPlane('plane/front', 'Front Plane', Transform())
    sketch = MakeBoxProfile('sketch/profile', 'AnchorSketch', plane.id, width, height, ids[:2])
    lengths = tuple(ParameterValue(value, ValueKind.KLength, 'mm') for value in (width, height, depth))
    boss = FeatureStep('feature/boss', 'AnchorBoss', FeatureKind.KExtrusion, 0, sketch_id=sketch.id,
                       parameter_ids=ids[2:], operation=BooleanOp.KCreate, definition=ExtrudeFeature(length=lengths[2]))
    parameters = tuple(Parameter(id, name, value, owner_id=owner) for id, name, value, owner in
                       zip(ids, ('D1', 'D2', 'D1'), lengths, (sketch.id, sketch.id, boss.id), strict=True))
    name = PureWindowsPath(settings['output']['path_name']).stem
    document = CadDocument(CadSource('kit-neutral', '<independent rectangle intent>', digest(canonical(intent))),
                           (Configuration('configuration/default', 'Default', active=True),), parameters, (plane,),
                           (sketch,), (), (boss,), (DesignBody('body/boss', boss.name, boss.id),), metadata={'name': name})
    document.AssertValid()
    return {'document': ToData(document), 'settings': settings,
            'rectangle_dimensions': {'width_text_m': [width * .0005, -height * .0003],
                                     'height_text_m': [width * .0013, height * .0005], 'route_centerline': False},
            'equation': {'dependency': ids[0], 'target': ids[2], 'divisor': intent['divisor']}}


def original_intent(private_source, lock):
    import AuthorEquationSources01 as equations

    seal = json.loads(checked(private_source / 'IntentSeal.json', SEAL))
    case = json.loads(checked(private_source / 'Intent.json', lock['intent_sha256']))
    equations.check_case(case, SLOT)
    require(seal['intent_sha256'] == lock['intent_sha256'] and 22.001 <= case['edit_width_mm'] <= 60.999
            and abs(case['edit_width_mm'] - case['width_mm']) >= 4., 'the independent slot intent differs')
    return case


def generate(root, private, job, pin, lock):
    import subprocess

    code = code_root(private, pin, job)
    require(all(not (private / name).exists() for name in ('Request.json', 'Candidate.SLDPRT', 'Generation.json', 'Evaluation.json')),
            'generation must occur once before comparison attachment')
    sealed_case = original_intent(Path(r'C:\KitEquationSource121') / SLOT, lock)
    neutral = {key: sealed_case[key] for key in ('width_mm', 'height_mm', 'depth_mm', 'divisor')}
    sys.path.insert(0, str(code / 'src'))
    supplied = canonical(request(neutral, json.loads((root / 'TargetSettings.json').read_bytes())))
    request_sha = publish(private / 'Request.json', supplied)
    scripts = code / RESEARCH
    emitter = scripts / 'equations/BuildWidthDepthPart.py'
    run = 'import runpy,sys; sys.path[:0]=sys.argv[2:]; runpy.run_path(sys.argv[1],run_name="__main__")'
    argv = [sys.executable, '-I', '-B', '-c', run, str(emitter), str(code), str(code / 'src'), str(scripts)]
    builds = [subprocess.run(argv, cwd=code, input=supplied, capture_output=True, timeout=60) for _ in range(2)]
    for index, child in enumerate(builds):
        publish(private / f'Writer{index}.stderr', child.stderr)
        require(child.returncode == 0, 'the isolated writer did not complete')
    assert_equal = builds[0].stdout == builds[1].stdout and builds[0].stderr == builds[1].stderr
    require(assert_equal, 'independent guarded writer outputs differ')
    proof = json.loads(builds[0].stderr)
    require(proof['runtime_input_file_reads'] == 0 and proof['expression'] == EXPRESSION and len(proof['streams']) == 10
            and proof['sha256'] == digest(builds[0].stdout) and proof['bytes'] == len(builds[0].stdout),
            'the writer output is outside the bounded native equation profile')
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    archive = SldprtArchive.from_bytes(builds[0].stdout)
    keys = tuple(ReadFileKey(ReadHeaderGraph(archive.require(name), 19000).FieldsValue['f38'])
                 for name in ('Contents/Config-0-ModelHeader', 'Header2'))
    require(archive.format_version == 4 and keys[0] == keys[1]
            and keys[0][:3] == (PureWindowsPath(job['target']).stem, job['target'], 2),
            'generated part does not own the actual C: staging locator')
    artifact = publish(private / 'Candidate.SLDPRT', builds[0].stdout)
    freeze = {'trial_sha256': pin, 'source_lock_sha256': LOCK, 'request_sha256': request_sha, 'candidate_sha256': artifact,
              'target': job['target'], 'repeated_guarded_builds': 2, 'runtime_input_file_reads': 0, 'proof': proof,
              'native_source_payloads_read': 0, 'comparison_prediction_or_receipts_read': 0}
    freeze_sha = publish(private / 'Generation.json', canonical(freeze))
    return {'generation_sha256': freeze_sha, 'candidate_sha256': artifact, 'guarded_writer_processes': 2,
            'runtime_input_file_reads': 0, 'comparison_payloads_read': 0, 'native_launches': 0}


def generation(private, pin, job, expected):
    raw = checked(private / 'Generation.json', expected)
    freeze = json.loads(raw)
    require(freeze['trial_sha256'] == pin and freeze['source_lock_sha256'] == LOCK and freeze['target'] == job['target']
            and freeze['repeated_guarded_builds'] == 2 and freeze['runtime_input_file_reads'] == 0
            and freeze['native_source_payloads_read'] == freeze['comparison_prediction_or_receipts_read'] == 0
            and freeze['candidate_sha256'] == freeze['proof']['sha256'], 'comparison cannot precede the writer freeze')
    checked(private / 'Candidate.SLDPRT', freeze['candidate_sha256'])
    checked(private / 'Request.json', freeze['request_sha256'])
    return freeze, digest(raw)


def source_receipts(source, lock):
    values = {}
    for phase in SOURCE_PHASES:
        expected = lock['phases'][phase]
        folder = source / 'Inspection' / phase
        checked(folder / 'Record.json', expected['record_sha256'])
        result = json.loads(checked(folder / 'Result.json', expected['result_sha256']))
        require(result['passed'] and result['slot'] == SLOT and result['phase'] == phase and result['writer_output_count'] == 0
                and result['intent_sha256'] == lock['intent_sha256'] and result['prediction_sha256'] == lock['prediction_sha256'],
                'the locked source lifecycle is not intact')
        values[phase] = result
    return values


def semantic_signature(state, vertices):
    import SdkCornerOwnerGraph as owners

    roles = owners.geometry_roles(state['geometry'], vertices)
    lines, points = ([tuple(value) for value in roles[key]] for key in ('line_ids', 'point_ids'))
    result = []
    for row in state['relations']:
        kind = row['kind']
        kinds = row['entity_types']
        keys = [tuple(key) for key in row['entity_ids']]
        require(not row['suppressed'] and len(kinds) == len(keys), 'foreign or suppressed source relation')
        if kind in (4, 5):
            require(kinds == [3] and len(keys) == 1 and keys[0] in lines, 'source axis relation lost its actual contour edge')
            result.append((kind, (lines.index(keys[0]),)))
        elif kind == 1:
            require(kinds == [2, 2] and all(key in points for key in keys),
                    'source dimension is not owned by its actual two corner points')
            result.append((kind, tuple(sorted(points.index(key) for key in keys))))
        else:
            require(kind == 9 and kinds == [2, 2] and len(keys) == 2 and points[0] in keys
                    and sum(key not in points for key in keys) == 1, 'source coincidence does not bind its separate origin and corner')
            result.append((kind, (0,)))
    required = [(1, (0, 1)), (1, (1, 2)), (4, (0,)), (4, (2,)), (5, (1,)), (5, (3,)), (9, (0,))]
    require(sorted(result) == required, 'source relation ownership lies outside the admitted origin rectangle')
    return json.loads(canonical(required))


def replay_source(payload, authored, code):
    sys.path[:0] = [str(code / 'src'), str(code / RESEARCH / 'equations')]
    import ReplayPartEquationConfig as replay
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from interchange.Features.FeatureExtrude import ExtrudeEnd

    archive = replay.SldprtArchive.from_bytes(payload)
    require(archive.format_version == 4, 'source lies outside ordinary 2026 format version 4')
    wire = archive.require(replay.CONFIG)
    header = replay.ReadHeaderGraph(archive.require(replay.HEADER), replay.VERSION)
    graph = replay.ReadConfigMut(wire, replay.VERSION, header, PartRelations=True)
    again, written = replay.WriteConfigMut(graph.RootValue, replay.VERSION, header, PartRelations=True)
    require(again == wire and replay.signature(graph) == replay.signature(written), 'native equation archive replay is not exact')
    relation = replay.inspect_relation(graph, authored)
    bindings = [token for side in relation['sides'] for token in side['tokens'] if 'binding_class' in token]
    require(relation['manager_dimension_cache_count'] == 0
            and all(token['local_reference'] and token['dependency_count'] == 0 for token in bindings),
            'source equation has an extra external component or dependency owner')
    feature_stream = replay.CONFIG + '-ResolvedFeatures'
    linked = replay.verify_resolved(archive, graph, relation, authored)
    cmgr = replay.ReadCmgrMut(archive.require('Contents/CMgr'), replay.VERSION)
    context = {'cmgr_f658': cmgr.RootValue.FieldsValue['f658'], 'model_compressed_stream': 1, 'model_is_part': 1}
    resolved = replay.ReadResolvedMut(archive.require(feature_stream), replay.VERSION, graph.MapValue, context)
    link = NativeLink(graph, resolved, replay.CONFIG, feature_stream)
    roots = IndexFeatures(link)
    (boss,) = (node for node in roots.values() if node.ClassValue.NameValue == 'moExtrusion_c')
    owner = ReadExtrude(link, boss, roots)
    frame = ReadPrismFrame(owner.ProfileValue, graph.RootValue, roots)
    coords = lambda point: (point.x, point.y, point.z)
    require(not owner.IsReversed and owner.ModeValue == ExtrudeEnd.KBlind and owner.SecondValue is None
            and len(owner.ParentsValue) == 1 and owner.ParentsValue[0] is owner.ProfileValue
            and tuple(map(coords, (frame.origin, frame.x_axis, frame.y_axis, frame.z_axis)))
            == ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.), (0., 0., 1.)),
            'the actual source must retain its forward blind Front-frame owner')
    wrappers = tuple(entry.EntryValue for entry in graph.MapValue.EntriesValue if isinstance(entry.EntryValue, ArchiveNode)
                     and entry.EntryValue.ClassValue.NameValue == 'moDimRefWrapper_c')
    handles = tuple(row.FieldsValue['f58'] for row in wrappers)
    require(len(handles) == 2 and len({key.FieldsValue['f58'] for key in handles}) == 2
            and all(key.FieldsValue['f58'].FieldsValue['owner'] is graph.RootValue for key in handles),
            'source equation operands lose the actual distinct local references')
    return {'config_sha256': digest(wire), 'resolved_sha256': linked['resolved_sha256'],
            'map_counters': [graph.MapValue.CounterValue, linked['resolved_map_counter']]}


def attach(private, job, pin, lock, generation_sha):
    import AuthorEquationSources01 as equations
    from InspectSdkBlindPart import tree_prediction
    from SdkCornerOwnerGraph import close

    code = code_root(private, pin, job)
    freeze, frozen_sha = generation(private, pin, job, generation_sha)
    require(not (private / 'Evaluation.json').exists(), 'comparison was already attached')
    source = Path(r'C:\KitEquationSource121') / SLOT
    case = original_intent(source, lock)
    raw = json.loads(checked(source / 'Prediction.json', lock['prediction_sha256']))
    require(raw == {'Original': equations.expected(case), 'Edited': equations.expected(case, True)},
            'the independent frozen analytic comparison differs')
    receipts = source_receipts(source, lock)
    neutral = json.loads(checked(private / 'Request.json', freeze['request_sha256']))
    tree = tree_prediction(neutral, {'intent': {'profile': 'AnchorSketch', 'feature': 'AnchorBoss', 'resolved_roots': 19}})
    source_payloads, source_roles = {}, {}
    for role, expected in raw.items():
        binary = checked(source / 'Native' / (role + '.SLDPRT'), lock['source_files'][role]['sha256'])
        require(len(binary) == lock['source_files'][role]['bytes'], 'immutable source file size differs')
        authored = receipts['Author']['observed'][role]
        reopened = receipts['Reopen' + role]
        state = reopened['observed'][role]
        require(reopened['open_status'] == [0, 0] and reopened['files'][role] == lock['source_files'][role],
                'the original locked source reopen lacks matching custody')
        for snapshot in (authored, state):
            require(snapshot['body_count'] == 1 and snapshot['configuration_names'] == ['Default']
                    and [[row['name'], row['type'], row['parent']] for row in snapshot['tree']] == tree
                    and not any(row['suppressed'] or row['error'] or row['warning'] for row in snapshot['tree']),
                    'the source feature tree or configuration is outside the predeclared authoring profile')
            (equation,) = snapshot['equations']
            require(equation['text'] == EXPRESSION and not equation['disabled'] and not equation['global_variable'],
                    'source equation is not its fixed enabled local relation')
            for index, name in enumerate(NAMES):
                dimension = snapshot['dimensions'][name]
                require(dimension['full_name'].rsplit('@', 1)[0] == name and not dimension['read_only']
                        and dimension['driven_state'] == (1 if index == 2 else 2)
                        and close(dimension['system_value_m'], expected['dimensions_m'][name]),
                        'locked native actual dimension owner or value differs')
            mass = snapshot['mass_properties']
            require(close(mass['volume'], expected['volume_m3']) and close(mass['area'], expected['area_m2'])
                    and all(close(a, b) for a, b in zip(mass['com'], expected['center_m'], strict=True)),
                    'locked native source geometry differs from the independent analytic recipe')
        source_roles[role] = semantic_signature(state, expected['corners_m'])
        source_payloads[role] = replay_source(binary, authored, code)
    base = raw['Original']
    edited = raw['Edited']
    evaluation = {'trial_sha256': pin, 'source_lock_sha256': LOCK, 'generation_sha256': frozen_sha,
                  'source_replay': source_payloads, 'source_constraint_roles': source_roles,
                  'source_geometry': {role: receipts['Reopen' + role]['observed'][role]['mass_properties'] for role in raw},
                  'tree': tree, 'expression': EXPRESSION, 'control': job['control'],
                  'case': {'profile': 'AnchorSketch', 'feature': 'AnchorBoss', 'support': 'Front Plane', 'origin': 'Origin',
                           'parameter_names': NAMES, 'configuration_name': 'Default', 'density_kg_m3': 1.0,
                           'vertices_m': base['corners_m'], 'dimensions_m': base['dimensions_m']},
                  'edits': {'Reference': {'parameter': NAMES[0], 'value_m': edited['dimensions_m'][NAMES[0]],
                                          'expected_dimensions_m': edited['dimensions_m']}},
                  'vertices': {role: row['corners_m'] for role, row in raw.items()}}
    seal = publish(private / 'Evaluation.json', canonical(evaluation))
    return {'comparison_sha256': seal, 'generation_sha256': frozen_sha, 'original_and_edited_lock_verified': True,
            'typed_source_replays': 2, 'native_launches': 0}


def receipt(private, role, pin):
    path = private / 'Inspection' / role / 'TrialReceipt.json'
    if not path.is_file():
        return None
    value = json.loads(path.read_bytes())
    require(value['trial_sha256'] == pin and value['role'] == role, 'the phase receipt belongs to a different evaluation')
    checked(path.with_name('Record.json'), value['record_sha256'])
    return value


def phases(private, exact, job, pin, role, generation_sha, comparison_sha):
    from AuthorCurves import EvidenceFailure
    import ObserveWidthDepthPart as controls
    import PrepareWidthDepthSameLocator as measured
    import SdkCornerOwnerGraph as owners

    freeze, artifact = generation(private, pin, job, generation_sha)
    comparison_raw = checked(private / 'Evaluation.json', comparison_sha)
    comparison = json.loads(comparison_raw)
    require(comparison['trial_sha256'] == pin and comparison['source_lock_sha256'] == LOCK
            and comparison['generation_sha256'] == artifact, 'the native evaluator requires the original frozen comparison')
    folder = private / 'Inspection' / role
    require(not folder.exists(), 'duplicate native phase')
    if role.startswith('Control'):
        checked(private / CONTROL, CONTROL_SHA)
        result = controls.inspect(private / 'Trial.json', {'cases': {role: job['control']}}, role)
        checked(private / CONTROL, CONTROL_SHA)
    else:
        index = PHASES.index(role)
        previous = receipt(private, PHASES[index - 1], pin)
        require(previous and previous['passed'], 'the preceding native phase must pass first')
        if role == 'ReferenceEdit':
            import Swapp

            Swapp.sweep()
            exact.parent.mkdir(parents=True, exist_ok=True)
            require(not exact.exists() and exact.resolve() == exact, 'generated native target must be absent and unredirected')
            publish(exact, checked(private / 'Candidate.SLDPRT', freeze['candidate_sha256']))
            source, expected, prior = exact, freeze['candidate_sha256'], None
        else:
            prior = previous['result']
            source = private / 'Inspection/ReferenceEdit/Edited.SLDPRT'
            expected = prior['derivative_sha256']
        checked(source, expected)
        result = measured.candidate_phase(private, comparison, role, source, expected, 'Reference', prior)
        checked(exact, freeze['candidate_sha256'])
        if result['passed']:
            try:
                for label, state in result['states'].items():
                    case = 'Original' if role == 'ReferenceEdit' and label != 'Edited' else 'Edited'
                    require(semantic_signature(state, comparison['vertices'][case]) == comparison['source_constraint_roles'][case],
                            'generated native rectangle relation roles differ from the separate locked source')
                    observed, wanted = state['mass'], comparison['source_geometry'][case]
                    require(all(owners.close(observed[key], wanted[key]) for key in ('volume', 'area')) and
                            all(owners.close(a, b) for a, b in zip(observed['com'], wanted['com'], strict=True)),
                            'generated native mass properties differ from the independent locked source')
            except (ValueError, EvidenceFailure) as error:
                result.update(passed=False, locked_source_comparison_error=repr(error))
    record = digest((folder / 'Record.json').read_bytes())
    identity = result.get('oracle_identity', {})
    exact_version = identity.get('sha256') == ORACLE and identity.get('file_version') == ORACLE_VERSION
    row = {'trial_sha256': pin, 'comparison_sha256': digest(comparison_raw), 'role': role,
           'record_sha256': record, 'passed': bool(result['passed'] and exact_version), 'result': result}
    evidence = publish(folder / 'TrialReceipt.json', canonical(row))
    report = {'role': role, 'passed': row['passed'], 'phase_sha256': evidence,
              'numeric_checks': result.get('numeric_check_count', result.get('numeric_checks', 0)),
              'open_status': result.get('open_status', [result.get('open_errors'), result.get('open_warnings')]),
              'process_birth': identity.get('process_creation_filetime')}
    return report


def summary(private, exact, job, pin, lock, generation_sha, comparison_sha):
    freeze, artifact = generation(private, pin, job, generation_sha)
    comparison = json.loads(checked(private / 'Evaluation.json', comparison_sha))
    require(comparison['generation_sha256'] == artifact and comparison['source_lock_sha256'] == LOCK,
            'summary comparison custody differs')
    source = Path(r'C:\KitEquationSource121') / SLOT
    original_intent(source, lock)
    checked(source / 'Prediction.json', lock['prediction_sha256'])
    source_receipts(source, lock)
    for role, entry in lock['source_files'].items():
        checked(source / 'Native' / (role + '.SLDPRT'), entry['sha256'])
    values = {role: receipt(private, role, pin) for role in PHASES}
    for row in values.values():
        require(row is None or row['comparison_sha256'] == comparison_sha, 'phase comparison hash changed')
    before, after = (values[role] for role in ('ControlBefore', 'ControlAfter'))
    controls = bool(before and after and before['passed'] and after['passed']
                    and before['result']['original'] == after['result']['original'])
    complete = all(row and row['passed'] for row in values.values())
    births = tuple(row['result'].get('oracle_identity', {}).get('process_creation_filetime') for row in values.values() if row)
    saved = None
    if complete:
        checked(exact, freeze['candidate_sha256'])
        saved = values['ReferenceEdit']['result']['derivative_sha256']
        checked(private / 'Inspection/ReferenceEdit/Edited.SLDPRT', saved)
    passed = bool(complete and controls and len(births) == 4 and all(type(item) is int for item in births)
                  and all(first < next for first, next in zip(births, births[1:])))
    public = {'schema': SCHEMA, 'trial_sha256': pin, 'source_lock_sha256': LOCK, 'writer_revision': WRITER_REV,
              'chronology': job['chronology'], 'generation_sha256': artifact, 'comparison_sha256': comparison_sha,
              'candidate_sha256': freeze['candidate_sha256'], 'saved_derivative_sha256': saved, 'passed': passed,
              'controls_healthy': controls, 'distinct_native_processes': len({stamp for stamp in births if type(stamp) is int}),
              'phase_record_sha256': {key: row['record_sha256'] for key, row in values.items() if row},
              'numeric_checks': sum(row['result'].get('numeric_check_count', row['result'].get('numeric_checks', 0))
                                    for row in values.values() if row),
              'scoped_heldout_acceptance': int(passed), 'public_writer_qualified': False, 'native_source_translation_qualified': False,
              'sealed_payloads_shared': 0}
    publish(private / 'Result.json', canonical(public))
    return public


def main():
    parser = argparse.ArgumentParser(description='Freeze and observe the separate locked width-depth equation family')
    sub = parser.add_subparsers(dest='command', required=True)
    host = sub.add_parser('prepare')
    host.add_argument('name')
    host.add_argument('creation_epoch', type=int)
    for name in ('verify', 'generate', 'attach', 'observe', 'summary'):
        step = sub.add_parser(name)
        if name == 'observe':
            step.add_argument('role', choices=PHASES)
        step.add_argument('packet', type=Path)
        step.add_argument('sha256')
        if name in ('attach', 'observe', 'summary'):
            step.add_argument('--generation-sha256', required=True)
        if name in ('observe', 'summary'):
            step.add_argument('--comparison-sha256', required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        require(os.name == 'posix', 'use the host to freeze public inputs and the tool closure')
        prepare(args.name, args.creation_epoch)
        return 0
    require(os.name == 'nt', 'only the root-owned Windows guest can run private phases')
    try:
        root, private, exact, job, lock = read_trial(args.packet, args.sha256)
        command = args.command
        if command == 'verify':
            status = verify(root, private, exact, job, args.sha256)
        elif command == 'generate':
            status = generate(root, private, job, args.sha256, lock)
        elif command == 'attach':
            status = attach(private, job, args.sha256, lock, args.generation_sha256)
        elif command == 'observe':
            status = phases(private, exact, job, args.sha256, args.role, args.generation_sha256, args.comparison_sha256)
        else:
            status = summary(private, exact, job, args.sha256, lock, args.generation_sha256, args.comparison_sha256)
        print(json.dumps(status, sort_keys=True))
        return 0 if status.get('passed', True) else 1
    except Exception as error:
        if 'private' in locals() and private.is_dir():
            failure = private / f'{args.command}-{getattr(args, "role", "setup")}.error.txt'
            if not failure.exists():
                publish(failure, repr(error).encode())
        print(json.dumps({'stage': args.command, 'failure_type': type(error).__name__, 'passed': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
