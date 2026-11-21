from argparse import ArgumentParser
from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, load
from math import isclose
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--default-body', action='store_true')
    args = parser.parse_args()
    case = load(sys.stdin)
    sys.path[:0] = [str(args.sdk/'src'), str(Path(__file__).resolve().parent/'Harness01')]
    from MakeAnchoredRequest import request
    from CheckAnchoredGraph import check_graph
    from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import AnchorPartInput
    from convert import open_document, write_document
    from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeAnchorNamed import MakeAnchorNamed
    from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeAnchorBase import MakeAnchorBase
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
    from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import MakeRectDimPart
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.adapters.solidworks.Core.Native import ParseKeywords
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.serialization.EncodeData import ToData
    from interchange.serialization.JsonCodec import DumpJson
    require(SldprtAdapter is not None, 'native reader did not preload')
    for name in ('ascii', 'utf-8', 'utf-16-le', 'utf-16-be', 'latin-1'):
        lookup(name)
    for name in ('interchange.document.Models.DocumentProvenance', 'interchange.document.Behavior.DocumentIo',
                 'interchange.brep.Validation.BrepValidate', 'interchange.document.Validation.DocumentAssemblyValidate',
                 'interchange.document.Validation.DocumentFeatureValidate', 'interchange.document.Validation.DocumentReferenceValidate'):
        import_module(name)
    document, settings, dimensions = request(case)
    anchor = AnchorPartInput(case['anchor_kind'], dimensions)
    if args.default_body:
        document = replace(document, bodies=(replace(document.bodies[0], name=document.feature_timeline[0].name),))
    source_before = sha256(DumpJson(document, IndentSize=None).encode()).hexdigest()
    plain_document = replace(document, bodies=(replace(document.bodies[0], name=document.feature_timeline[0].name),))
    guard = {'enabled': False, 'attempts': []}

    def audit(event, arguments):
        if guard['enabled'] and (event == 'open' or event.startswith(('subprocess.', 'socket.'))
            or event in ('os.system', 'os.fork', 'os.posix_spawn', 'ctypes.dlopen')):
            guard['attempts'].append({'event': event, 'arguments': repr(arguments[:2])})
            raise RuntimeError('named construction attempted runtime file process or network access')

    sys.addaudithook(audit)
    guard['enabled'] = True
    try:
        plain = MakeAnchorBase(plain_document, settings, anchor)
        candidate = MakeAnchorNamed(document, settings, anchor)
        changed = sorted(name for name, value in candidate.StreamsValue.items() if plain.StreamsValue[name] != value)
        expected_changed = [] if args.default_body else ['Contents/Config-0', 'Contents/Config-0-ResolvedFeatures']
        require(changed == expected_changed, 'named output changed an unrelated logical stream')
        if args.default_body:
            require(candidate.BytesValue == plain.BytesValue, 'default body no longer follows the exact original composer')
        if case.get('expected_named_sha256') and not args.default_body:
            require(sha256(candidate.BytesValue).hexdigest() == case['expected_named_sha256'], 'typed port changed the prior native-qualified named bytes')
        if case.get('expected_plain_sha256'):
            require(sha256(plain.BytesValue).hexdigest() == case['expected_plain_sha256'], 'typed port changed the prior native-qualified plain bytes')
        streams = candidate.StreamsValue
        require(set(streams) == {'Header2', 'Contents/Config-0-ModelHeader', 'Contents/Config-0',
            'Contents/CMgr', 'Contents/CMgrHdr2', 'Contents/Config-0-ResolvedFeatures', 'Contents/Definition',
            '_MO_VERSION_19000/Biography', '_MO_VERSION_19000/History', 'swXmlContents/KeyWords'},
            'named output does not have the exact generated cache free stream inventory')
        model, boss = candidate.SystemValue.RootValue, candidate.BossValue.FeatureValue
        manager = model.FieldsValue['fd88']
        require(candidate.ConfigValue.RootValue is model and candidate.ResolvedValue.RootsValue[-1] is boss,
                'named output lost actual generated model and feature ownership')
        atom_summary = None
        if not args.default_body:
            atom, = [entry['o'] for entry in manager['atoms']]
            require(boss.FieldsValue['f528']['items'][0]['o'] is atom and boss.FieldsValue['n494'] == 1
                and boss.FieldsValue['f498'] == [{'v': atom.FieldsValue['f140']}]
                and atom.FieldsValue['f140'] == manager['f260']
                and atom.FieldsValue['f130'] == atom.FieldsValue['f12c'] == boss.FieldsValue['f08']
                and atom.FieldsValue['body_kind'] == 0 and 'f160' not in atom.FieldsValue
                and atom.FieldsValue['f18'].FieldsValue['f08'] == document.bodies[0].name,
                'named output lost actual cross domain atom ownership')
            atom_summary = {name: atom.FieldsValue[name] for name in
                ('f08', 'f140', 'f144', 'f130', 'f12c', 'f158', 'body_kind',
                 'f170', 'f18c', 'f198', 'f180', 'f188', 'f1b0', 'f19c')}
        archive = SldprtArchive.from_bytes(candidate.BytesValue)
        require(archive.streams == streams, 'generated named container changed its logical streams')
        header = ReadHeaderGraph(streams['Contents/Config-0-ModelHeader'], 19000)
        config = ReadConfigMut(streams['Contents/Config-0'], 19000, header)
        cmgr = ReadCmgrMut(streams['Contents/CMgr'], 19000)
        context = MakeLinkContext(config, cmgr)
        resolved = ReadResolvedMut(streams['Contents/Config-0-ResolvedFeatures'], 19000, config.MapValue, context)
        config_bytes, config_again = WriteConfigMut(config.RootValue, 19000, header)
        resolved_bytes, _ = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, config_again.MapValue, context)
        require(config_bytes == streams['Contents/Config-0'] and resolved_bytes == streams['Contents/Config-0-ResolvedFeatures'],
                'generated named owners do not round trip complete typed streams')
        if not args.default_body:
            loaded_atom, = [entry['o'] for entry in config.RootValue.FieldsValue['fd88']['atoms']]
            require(resolved.RootsValue[-1].FieldsValue['f528']['items'][0]['o'] is loaded_atom
                and loaded_atom.FieldsValue['f18'].FieldsValue['f08'] == document.bodies[0].name,
                'typed readback lost actual output alias or utf16 name')
        require(all(row['completed'] and not row['missing_schemas'] and not row['provisional_schemas']
                    for row in (config.ReportValue, resolved.ReportValue, candidate.ConfigValue.ReportValue, candidate.ResolvedValue.ReportValue)),
                'named construction reached unqualified archive grammar')
        graph_proof = check_graph(candidate, case['anchor_kind'], document)
        _, features = ParseKeywords(streams['swXmlContents/KeyWords'])
        keyword_dims = [(feature.name, dimension.name, dimension.value_mm)
                        for feature in features for dimension in feature.dimensions]
        drivers = [(document.sketches[0].name, parameter.name, parameter.value.value) for parameter in document.parameters[:2]]
        drivers.append((document.feature_timeline[0].name, document.parameters[2].name, document.parameters[2].value.value))
        require(len(keyword_dims) == len(drivers) and {(owner, name) for owner, name, _ in keyword_dims}
                == {(owner, name) for owner, name, _ in drivers}, 'keyword and actual driver owners disagree')
        for owner, name, value in drivers:
            expected = next(item[2] for item in keyword_dims if item[:2] == (owner, name))
            require(isclose(value, expected, rel_tol=1e-12), 'keyword and actual driver values disagree')
        strict_reader = {'not_evaluated': True, 'reason': 'complete_center_public_projection_is_separately_unqualified'}
        gate = None
        if not args.default_body:
            supported = SldprtWriter().supports(document, BytesIO())
            require(not supported, 'private named constructor became publicly registered')
            sink = BytesIO()
            try:
                write_document(document, sink, destination_format='solidworks.sldprt', allow_carrier=False)
            except Exception as error:
                gate = {'supports': supported, 'error': {'class': type(error).__name__, 'message': str(error)}, 'output_bytes': len(sink.getvalue())}
            require(gate is not None and not sink.getvalue(), 'unregistered named profile produced public writer bytes')
    finally:
        guard['enabled'] = False
    source_after = sha256(DumpJson(document, IndentSize=None).encode()).hexdigest()
    require(source_before == source_after, 'portable input was mutated during generation')
    source_root = (args.sdk/'src').resolve()
    outside, research = [], []
    for name, module in tuple(sys.modules.items()):
        filename = getattr(module, '__file__', None)
        if name.startswith(('convert', 'interchange')) and filename and not Path(filename).resolve().is_relative_to(source_root):
            outside.append(name)
        if filename and '/re/tooling/' in str(filename):
            research.append(name)
    require(not guard['attempts'] and not outside and not research, 'named construction runtime or source-origin guard failed')
    result = {'schema': 'kit.sw2026.typed-anchored-named-output-build.v1', 'passed': True, 'case': case['name'],
        'default_body': args.default_body, 'anchor_kind': case['anchor_kind'], 'anchor_graph': graph_proof, 'neutral_document': ToData(document), 'spec': case['part'],
        'driver_names': case['driver_names'], 'artifact_sha256': sha256(candidate.BytesValue).hexdigest(),
        'artifact_bytes': len(candidate.BytesValue), 'blob': b64encode(candidate.BytesValue).decode('ascii'),
        'plain_artifact_sha256': sha256(plain.BytesValue).hexdigest(), 'atom': atom_summary,
        'streams': {name: {'bytes': len(value), 'sha256': sha256(value).hexdigest()} for name, value in streams.items()},
        'logical_stream_difference': changed, 'typed_roundtrip_exact': True, 'cross_stream_alias_exact': True,
        'public_driver_rows': drivers, 'keyword_dimensions': keyword_dims, 'strict_ascii_reader': strict_reader,
        'writer_registration_gate': gate, 'source_document_unchanged': True, 'runtime_access_attempts': guard['attempts'],
        'unexpected_sdk_origins': outside, 'research_runtime_imports': research, 'heldout_inputs_read': 0,
        'native_acceptance': False, 'unicode_cacheless_reader_qualified': False, 'public_writer_enabled': False}
    print(dumps(result, ensure_ascii=True, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
