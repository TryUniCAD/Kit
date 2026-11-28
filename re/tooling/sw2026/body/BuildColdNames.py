from argparse import ArgumentParser
from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from json import dump, load
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--unnamed-control', action='store_true')
    args = parser.parse_args()
    spec = load(sys.stdin)
    sys.path[:0] = [str(args.sdk / 'src'), str(Path(__file__).resolve().parent)]
    from MakeColdNamedPart import construct
    from MakeColdRequest import make_request, prediction
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from interchange.serialization.EncodeData import ToData
    for name in ('ascii', 'utf-8', 'utf-16-le', 'utf-16-be', 'latin-1'):
        lookup(name)
    for name in ('interchange.document.Models.DocumentProvenance',
                 'interchange.document.Behavior.DocumentIo',
                 'interchange.document.Validation.DocumentAssemblyValidate',
                 'interchange.document.Validation.DocumentFeatureValidate',
                 'interchange.document.Validation.DocumentReferenceValidate'):
        import_module(name)
    document, settings = make_request(spec)
    document.assert_valid()
    if args.unnamed_control:
        document = replace(document, bodies=(replace(document.bodies[0],
                            name=document.feature_timeline[0].name),))
    guard = {'enabled': False, 'attempts': []}

    def audit(event, arguments):
        if guard['enabled'] and event == 'open':
            guard['attempts'].append(repr(arguments[:2]))
            raise RuntimeError('cold name construction attempted an additional file access')

    sys.addaudithook(audit)
    guard['enabled'] = True
    try:
        if args.unnamed_control:
            candidate = MakeBlindPart(document, settings)
            plain_bytes, plain_streams = candidate.BytesValue, candidate.StreamsValue
        else:
            candidate, plain_bytes, plain_streams = construct(document, settings)
        streams = candidate.StreamsValue
        expected_names = {'Header2', 'Contents/Config-0-ModelHeader', 'Contents/Config-0',
            'Contents/CMgr', 'Contents/CMgrHdr2', 'Contents/Config-0-ResolvedFeatures',
            'Contents/Definition', '_MO_VERSION_19000/Biography',
            '_MO_VERSION_19000/History', 'swXmlContents/KeyWords'}
        require(set(streams) == expected_names, 'cold output is not the exact generated no-cache stream set')
        changed = sorted(name for name, value in streams.items() if plain_streams[name] != value)
        expected_changed = [] if args.unnamed_control else ['Contents/Config-0', 'Contents/Config-0-ResolvedFeatures']
        require(changed == expected_changed, 'cold atom changed an unrelated logical stream')
        model = candidate.SystemValue.RootValue
        boss = candidate.BossValue.FeatureValue
        manager = model.FieldsValue['fd88']
        require(candidate.ConfigValue.RootValue is model
            and candidate.ResolvedValue.RootsValue[-1] is boss
            and len(candidate.ResolvedValue.RootsValue) == 19,
            'cold output lost actual model and feature ownership')
        atom_summary = None
        if not args.unnamed_control:
            atom, = [entry['o'] for entry in manager['atoms']]
            require(boss.FieldsValue['f528']['items'][0]['o'] is atom
                and boss.FieldsValue['n494'] == 1
                and boss.FieldsValue['f498'] == [{'v': atom.FieldsValue['f140']}]
                and atom.FieldsValue['f140'] == manager['f260']
                and atom.FieldsValue['f130'] == atom.FieldsValue['f12c'] == boss.FieldsValue['f08']
                and atom.FieldsValue['body_kind'] == 0 and 'f160' not in atom.FieldsValue
                and atom.FieldsValue['f18'].FieldsValue['f08'] == document.bodies[0].name,
                'cold name constructor lost its actual atom or reciprocal output id domain')
            atom_summary = {name: atom.FieldsValue[name] for name in
                ('f08', 'f140', 'f144', 'f130', 'f12c', 'f158', 'body_kind',
                 'f170', 'f18c', 'f198', 'f180', 'f188', 'f1b0', 'f19c')}
        archive = SldprtArchive.from_bytes(candidate.BytesValue)
        require(archive.streams == streams, 'cold container changed its constructed logical streams')
        header = ReadHeaderGraph(streams['Contents/Config-0-ModelHeader'], 19000)
        config = ReadConfigMut(streams['Contents/Config-0'], 19000, header)
        cmgr = ReadCmgrMut(streams['Contents/CMgr'], 19000)
        context = MakeLinkContext(config, cmgr)
        resolved = ReadResolvedMut(streams['Contents/Config-0-ResolvedFeatures'],
                                   19000, config.MapValue, context)
        config_bytes, config_again = WriteConfigMut(config.RootValue, 19000, header)
        resolved_bytes, _ = WriteResolMut(resolved.RootsValue, resolved.ExtraFields,
                                          19000, config_again.MapValue, context)
        require(config_bytes == streams['Contents/Config-0']
            and resolved_bytes == streams['Contents/Config-0-ResolvedFeatures'],
            'cold model and output objects are not an exact typed wire round trip')
        if not args.unnamed_control:
            loaded_manager = config.RootValue.FieldsValue['fd88']
            loaded_atom, = [entry['o'] for entry in loaded_manager['atoms']]
            loaded_boss = resolved.RootsValue[-1]
            require(loaded_boss.FieldsValue['f528']['items'][0]['o'] is loaded_atom
                and loaded_boss.FieldsValue['f498'] == [{'v': loaded_atom.FieldsValue['f140']}]
                and loaded_atom.FieldsValue['f18'].FieldsValue['f08'] == spec['body_label'],
                'cold wire reader lost the cross-stream atom identity or authored name')
        require(all(row['completed'] and not row['missing_schemas'] and not row['provisional_schemas']
                    for row in (config.ReportValue, resolved.ReportValue,
                                candidate.ConfigValue.ReportValue, candidate.ResolvedValue.ReportValue)),
                'cold name construction reached unqualified archive grammar')
    finally:
        guard['enabled'] = False
    source_root = (args.sdk / 'src').resolve()
    outside = []
    research = []
    for name, module in sys.modules.items():
        filename = getattr(module, '__file__', None)
        if name.startswith(('convert', 'interchange')) and filename and not Path(filename).resolve().is_relative_to(source_root):
            outside.append(name)
        if filename and '/re/tooling/' in str(filename):
            research.append(name)
    require(not guard['attempts'] and not outside and not research, 'cold generation source or file guard failed')
    result = {'schema': 'kit.sw2026.cold-named-body-generated-discovery.v1',
        'passed': True, 'unnamed_control': args.unnamed_control,
        'neutral_document': ToData(document), 'spec': spec, 'prediction': prediction(spec),
        'tree_request': {'settings': {'system': {
            'folders': settings.SystemValue.FolderValues,
            'planes': dict(settings.SystemValue.PlaneNames),
            'cabinet_name': settings.SystemValue.CabinetName,
            'origin_name': settings.SystemValue.OriginName}}},
        'artifact_sha256': sha256(candidate.BytesValue).hexdigest(),
        'artifact_bytes': len(candidate.BytesValue), 'blob': b64encode(candidate.BytesValue).decode('ascii'),
        'plain_artifact_sha256': sha256(plain_bytes).hexdigest(),
        'streams': {name: {'bytes': len(value), 'sha256': sha256(value).hexdigest(),
                            'data': b64encode(value).decode('ascii')}
                    for name, value in streams.items()},
        'logical_stream_difference': changed, 'atom': atom_summary,
        'manager_counter': manager['f260'], 'manager_last_version': manager['fa8'],
        'typed_roundtrip_exact': True, 'cross_stream_alias_exact': True,
        'runtime_input_file_reads': len(guard['attempts']), 'unexpected_sdk_origins': outside,
        'research_runtime_imports': research, 'heldout_inputs_read': 0,
        'native_acceptance': False, 'named_body_writer_qualified': False,
        'strict_no_cache_name_reader_qualified': False}
    dump(result, sys.stdout, sort_keys=True, allow_nan=False)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
