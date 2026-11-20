from argparse import ArgumentParser
from base64 import b64decode, b64encode
import codecs
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
TOOLS = HERE.parents[2]
PACKET = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover/RadialConcentricDisplay04')
AT = '97656af81560dc37f3fd10a176afa39a69e05b02'
NATIVE = 'd128bf6b61c69b3525743c596ee2d20a02f7b5d4b41c4d28ab088c0bc8300009'
TRIAL = 'ac2696da314b7e2d4939fd75664270acecfe0274a479eafb9c2c6d5440aaed4b'
STREAM = 'ThirdPtyStore/VisualStates'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(data):
    return sha256(data).hexdigest()


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), 'missing or redirected disclosed input: ' + path.name)
    data = path.read_bytes()
    require(digest(data) == expected, 'disclosed input digest differs: ' + path.name)
    return data


def inspect_store(parent, requested, registry):
    from defs.Visual import load_visual_states, store_visual_states
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Assembly.Assembly import XmlRoot
    from convert.adapters.solidworks.Assembly.Display.ReadDisplayXml import ReadDispMember
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey, ReadFileText
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(parent)
    data = archive.require(STREAM)
    with registry.track_usage('load', STREAM, sources=archive.streams) as load:
        document, reader = load_visual_states(data, registry)
    with registry.track_usage('store', STREAM) as store:
        roundtrip = store_visual_states(document, registry)
    reports = [load.snapshot(), store.snapshot()]
    require(roundtrip == data and not document.tail and all(
        row['completed'] and not row['raw_operations'] and not row['missing_schemas'] for row in reports), 'independent visual stream did not replay exactly')
    root = document.head['root'].f
    link = ReadNativeLink(archive, 0)
    config = ReadCmgrMut(archive.require('Contents/CMgr'), 19000).RootValue.FieldsValue['f360']
    header = link.ConfigValue.HeaderValue
    top = ReadHeaderGraph(archive.require('Header2'), 19000)
    file_key = ReadFileKey(header.FieldsValue['f38'])
    direct = link.ConfigValue.RootValue.FieldsValue['f68']['list']['items']
    occurrences = {row['o'].FieldsValue['f08']: row['o'] for row in direct}
    order = tuple(occurrences)
    xml = XmlRoot(archive.require('swXmlContents/COMPINSTANCETREE'))
    ns = '{http://www.solidworks.com/sw2003/schema}'
    members = tuple(ReadDispMember(row) for row in xml.iter(ns + 'swReference'))
    require(tuple((row.FeatureId, row.NativeName) for row in members)
            == tuple((key, ReadNodeName(occurrences[key])) for key in order)
            and xml.find('.//' + ns + 'swDisplayStateList') is None, 'base XML and actual component owners differ')
    keys = tuple(range(1, len(requested) + 1))
    require(root['f118'] == [{'key': config.FieldsValue['f08'], 'value': keys[0], 'one': 1}]
            and [(item['id'], item['name']) for item in root['f0f0']] == [(key, name) for key, (name, _) in zip(keys, requested, strict=True)]
            and (root['n_comps'], root['n_ents'], root['n_f88'], root['n']) == (2, 3, 0, 0), 'visual selected configuration, authored names or owner counts differ')
    mapped, shared, props = [], [], []
    for row in root['comps']:
        context = row['comp'].f
        chain = context['f20'].f
        (target,) = chain['f08'].f['f08']
        feature, file = target['o'].f, context['f40'].f
        ident = feature['f44']
        actual = occurrences[ident]
        name = ReadNodeName(actual)
        require(context['owner'] is None and context['f30'] == (101 + actual.FieldsValue['f3f0']) & 0xffffffff
                and chain['f24'] == 1 and file['f58'] == 0 and feature['f50'] is None
                and ReadFileText(feature['f38']) == name and ReadFileText(file['shared']['h18']) == file_key[1],
                'visual state context lost the live parent and occurrence identity')
        require(all(file['shared'][key] is feature['f10'][key] for key in ('h18', 'h10')), 'visual parent handles lost their actual alias')
        shared.extend(file['shared'][key] for key in ('h18', 'h10'))
        actions = []
        for key, attr, (_, visibility) in zip(keys, row['attrs'], requested, strict=True):
            property_value, visual, label = (item['o'] for item in attr['objs'])
            props.append(property_value)
            require(attr['key'] == key and attr['k'] == 3 and visual.f['f10'] == int(dict(visibility)[name])
                    and (visual.f['f08'], visual.f['f14'], visual.f['f18'], visual.f['f1c']) == (keys[0], 6, 0, 1)
                    and label.f == {'f08': keys[0], 'f10': '<Default>_Display State 1', 'f18': keys[0]},
                    'visual state is not bound to the actual occurrence in authored order')
            actions.append(visual.f['f10'])
        mapped.append([ident, name, actions])
    require([row[0] for row in mapped] == list(reversed(order)) and shared[0] is shared[2] and shared[1] is shared[3],
            'visual store lost reverse occurrence order or pooled parent handles')
    actual_planes = [node.FieldsValue['f08'] for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == 'moRefPlane_c']
    planes, components = [], []
    for row in root['f78']:
        reference = row['ref'].f
        key, epoch = reference['ff0']['f00'], reference['ff0']['f08']
        require(DatumTime(header, key) == DatumTime(top, key) == epoch and reference['f58'].f == {'owner': None, 'has_ext': 0},
                'visual datum lost the real empty creation-log and local reference rules')
        planes.append([key, epoch])
        components.append(reference['f58'])
        for state, attr in zip(keys, row['attrs'], strict=True):
            property_value, visual = (item['o'] for item in attr['objs'])
            props.append(property_value)
            require(attr['key'] == state and attr['k'] == 2
                    and visual.f == {'f08': keys[0], 'f10': 0, 'f14': 6, 'f18': 1, 'f1c': 0},
                    'visual datum attribute differs')
    require([row[0] for row in planes] == list(reversed(actual_planes)) and len({id(node) for node in components}) == 3
            and len({id(node) for node in props}) == 1 and props[0].f == {'f08': keys[0], 'f10': None},
            'visual datum order or actual null property alias differs')
    return {'bytes': len(data), 'sha256': digest(data), 'terminal_map': reader.count, 'exact_replay': True,
            'all_objects_typed': True, 'xml_occurrences': list(order), 'visual_occurrences': mapped,
            'visual_planes': planes, 'configuration': [config.FieldsValue['f08'], ReadNodeName(config)],
            'states': [[row['id'], row['name']] for row in root['f0f0']]}


def worker():
    request = json.load(sys.stdin)
    sys.path[:0] = [str(REPO / 'src'), str(TOOLS), str(TOOLS / 'serial'), str(HERE.parent)]
    import PrepareRadialConcentric as radial
    from Classes import registry
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import AsmDisplayIn
    from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    document = radial.FromData(request['neutral']['document'])
    child, = (row.document for row in document.assembly.documents)
    document.assert_valid()
    child.assert_valid()
    GetDocumentCaps(child)
    for encoding in ('utf-16-le', 'utf-16-be', 'cp1252', 'utf-8'):
        codecs.lookup(encoding)
    lights = radial.read_intents(request['neutral']['lighting'], request['epoch'])
    args = (document, child, 'Lights and Cameras', lights, request['locator'], request['epoch'])
    values = tuple(AsmDisplayIn(name, tuple((key, flag) for key, flag in rows)) for name, rows in request['display'])
    original_emit, original_recipe = radial.EmitAsmStreams, radial.MakeAsmRecipe
    active, attempts = False, []

    def audit(event, args):
        if active and (event in {'open', 'os.listdir', 'os.scandir', 'os.system', 'os.posix_spawn', 'os.fork', 'os.exec'}
                       or event.startswith(('socket.', 'subprocess.', 'ctypes.', 'winreg.'))):
            attempts.append(event)
            raise PermissionError('SDK visibility attempted external runtime access: ' + event)

    sys.addaudithook(audit)

    def build(rows, *, probe=None, moved=False):
        nonlocal active

        def apply(state, part, metadata, headers, references, mates):
            active_fields = state.ManagerValue.FieldsValue
            if probe == 'manager-locator':
                active_fields['f1f8'] = request['locator']
            elif probe == 'configuration-alias':
                config = state.CurrentConfig
                active_fields['f368'] = ArchiveNode(config.ClassValue, dict(config.FieldsValue))
            elif probe == 'source-chronology':
                for header in headers:
                    logs = header.FieldsValue['f20'].FieldsValue
                    logs['items'] = (*logs['items'], MakeRootLog(state.PlaneValues['z'], metadata.HeaderValue))
            elif probe == 'flag-eight-context':
                context = state.CurrentConfig.FieldsValue['fce8'][1]['o'].FieldsValue['f10']
                context.FieldsValue['f40'].FieldsValue['f58'] = 8
            elif probe == 'child-appearance':
                part = replace(part, StreamsValue=part.StreamsValue | {STREAM: b''})
            elif probe == 'unbound-header':
                file = headers[1].FieldsValue['f38']
                headers[1].FieldsValue['f38'] = ArchiveNode(file.ClassValue, dict(file.FieldsValue))
            elif probe == 'locked-mate':
                mates[0].FieldsValue['f4b8'] = 1
            return original_emit(state, part, metadata, headers, references, mates, DisplayValues=rows)

        def moved_recipe(*args):
            recipe = original_recipe(*args)
            return replace(recipe, SystemValue=replace(recipe.SystemValue, HasEmptyExplodedView=True))

        radial.EmitAsmStreams = apply
        if moved:
            radial.MakeAsmRecipe = moved_recipe
        try:
            active = True
            return radial.guarded_bundle(*args)
        finally:
            active = False
            radial.EmitAsmStreams, radial.MakeAsmRecipe = original_emit, original_recipe

    results = {}
    for name, intent, shifted in (
        ('plain', None, False), ('native', values, False), ('shifted_plain', None, True),
        ('shifted', (values[0], replace(values[2], NameValue='Gauge alignment'), replace(values[1], NameValue='Fixture access')), True),
    ):
        files, report = build(intent, moved=shifted)
        require(report['builds'] == 2 and report['runtime_io_attempts'] == 0, 'guarded shared assembly pair did not build twice')
        result = {'files': {role: b64encode(payload).decode() for role, payload in files.items()}, 'assembly': report}
        if intent is not None:
            rows = tuple((value.NameValue, value.VisibilityValues) for value in intent)
            result['store'] = inspect_store(files['parent'], rows, registry())
        results[name] = result
    for plain, named in (('plain', 'native'), ('shifted_plain', 'shifted')):
        before, after = (SldprtArchive.from_bytes(b64decode(results[name]['files']['parent'], validate=True)).streams for name in (plain, named))
        require(STREAM not in before and after.keys() - before.keys() == {STREAM}
                and {name for name in before if before[name] != after[name]} == set(), 'display intent changed existing assembly or XML bytes')
        require(results[plain]['files']['child'] == results[named]['files']['child'], 'display intent changed the shared child')
        results[named]['unchanged_parent_streams'] = len(before)
    require(results['native']['store']['xml_occurrences'] != results['shifted']['store']['xml_occurrences'],
            'shifted authored assembly did not instantiate new occurrence IDs')
    failures = {}
    bad_inputs = {
        'no-states': (),
        'wrong-default': (replace(values[0], VisibilityValues=values[1].VisibilityValues), *values[1:]),
        'foreign-name': (values[0], replace(values[1], VisibilityValues=(('foreign', True), values[1].VisibilityValues[1])), values[2]),
        'numeric-flag': (values[0], replace(values[1], VisibilityValues=((values[1].VisibilityValues[0][0], 1), values[1].VisibilityValues[1])), values[2]),
        'duplicate-state': (values[0], values[1], replace(values[2], NameValue=values[1].NameValue.upper())),
        'duplicate-vector': (values[0], values[1], replace(values[2], VisibilityValues=values[1].VisibilityValues)),
    }
    scopes = ('manager-locator', 'configuration-alias', 'source-chronology', 'flag-eight-context', 'child-appearance', 'unbound-header', 'locked-mate')
    for label in (*bad_inputs, *scopes):
        try:
            build(bad_inputs.get(label, values), probe=label if label in scopes else None)
        except ValueError as error:
            require('assembly vis' in str(error) or 'assembly display' in str(error), 'negative took a different path: ' + label + ': ' + str(error))
            failures[label] = str(error)
        else:
            raise ValueError('assembly emit unexpectedly accepted: ' + label)
    require(not attempts, 'guarded assembly replay attempted external access')
    return {'cases': results, 'refusals': failures, 'runtime_external_accesses': len(attempts)}


def verify(output):
    require(not output.exists(), 'choose a new proof output')
    native = json.loads(checked(REPO / 're/solidworks/measurements/2026/ConcentricRadialDisplayStoresNative01.json', NATIVE))['cases']['store-only']
    trial = json.loads(checked(PACKET / 'Trial.json', TRIAL))
    require(native['variant_passed'] and native['controls_healthy'] and native['native_processes'] == 5
            and native['candidate_numeric_checks'] == 84 and native['trial_sha256'] == TRIAL
            and trial['display_mode'] == 'store-only' and trial['heldout_inputs_read'] == 0, 'native-tested disclosed reference packet differs')
    source = json.loads(checked(PACKET / 'Evidence/Neutral.json', trial['files_sha256']['Evidence/Neutral.json']))
    original = json.loads(checked(PACKET / 'Evidence/Build.json', native['build_sha256']))
    sys.path.insert(0, str(REPO / 'src'))
    from interchange.serialization.Deserialize import FromData

    neutral = FromData(source['document'])
    occurrence_names = tuple(row.name for row in neutral.assembly.instances)
    request = {'neutral': source, 'epoch': original['authored_epoch'], 'locator': original['same_final_links']['parent']['file_key'][1],
               'display': [(name, list(zip(occurrence_names, map(bool, vector), strict=True))) for name, vector in trial['authored_states']]}

    def source_manifest(path):
        return {file.relative_to(REPO).as_posix(): digest(file.read_bytes()) for file in sorted(path.rglob('*'))
                if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc'}

    manifest = source_manifest(REPO / 'src')
    command = [sys.executable, '-I', '-B', str(HERE), 'worker']
    first, second = (subprocess.check_output(command, input=wire(request), timeout=180) for _ in range(2))
    require(first == second and manifest == source_manifest(REPO / 'src'), 'separate guarded processes disagreed or SDK source changed')
    report = json.loads(first)
    cases = report['cases']
    names = trial['working_names']
    old = checked(PACKET / 'OldBranch' / names['parent'], native['baseline_sha256'])
    exact = {role: checked(PACKET / 'Frozen' / names[role], native['generated_sha256'][role]) for role in names}
    require(b64decode(cases['plain']['files']['parent']) == old and all(
        b64decode(cases['native']['files'][role]) == data for role, data in exact.items())
        and cases['native']['store']['sha256'] == native['affected_stream']['variant_sha256'],
        'normal SDK did not reproduce the full native-tested parent, child and unchanged baseline')
    for case in cases.values():
        case['files'] = {role: digest(b64decode(data)) for role, data in case['files'].items()}
    proof = {'schema': 'kit.sw2026.sdk-concentric-visual-generation.v1', 'passed': True, 'source_base': AT,
             'sdk_source_count': len(manifest), 'sdk_source_sha256': digest(wire(manifest)), 'tool_sha256': digest(HERE.read_bytes()),
             'native_receipt_sha256': NATIVE, 'native_disclosed_trial_sha256': TRIAL, 'authored_request_sha256': digest(wire(request)),
             'native_exact_complete_pair': True, 'no_intent_exact_complete_baseline': True, 'workers': 2, 'guarded_complete_builds': 16,
             'heldout_credit': 0, 'source_equivalence': False, 'public_writer_qualified': False, 'new_native_processes': 0, **report}
    data = wire(proof)
    with output.open('xb') as stream:
        stream.write(data)
    return {'passed': True, 'result_sha256': digest(data), 'refusals': len(report['refusals']), 'native_exact': True}


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('verify').add_argument('output', type=Path)
    commands.add_parser('worker')
    args = parser.parse_args()
    sys.stdout.buffer.write(wire(worker() if args.action == 'worker' else verify(args.output)))


if __name__ == '__main__':
    main()
