from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
import sys


def digest(data):
    return sha256(data).hexdigest()


def unicode_value(units):
    data = b''.join(value.to_bytes(2, 'little') for value in units)
    try:
        text = data.decode('utf-16-le')
        return {'text': text, 'valid_utf16': text.encode('utf-16-le') == data,
                'code_units': units}
    except UnicodeError as error:
        return {'text': None, 'valid_utf16': False, 'code_units': units, 'error': str(error)}


def main():
    parser = ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--result-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    job_data = (args.packet / 'Trial.json').read_bytes()
    if digest(job_data) != '9e8d5bdebea994c735a7aa378146767ccfaf518ba0b3c7001913013ed7ff01a9':
        raise ValueError('frozen disclosed unicode author method differs')
    result_data = (args.packet / 'Inspection/Result.json').read_bytes()
    if digest(result_data) != args.result_sha256:
        raise ValueError('disclosed unicode native result differs')
    job, result = loads(job_data), loads(result_data)
    if not result['passed'] or not result['controls_healthy'] or result['distinct_processes'] != 8:
        raise ValueError('unicode ownership requires the complete healthy native source cohort')
    sys.path[:0] = [str(args.sdk / 'src'), str(Path(__file__).resolve().parent)]
    from ReadRawNameKernel import read_active
    from convert.Geometry.Parasolid import DecodePartData
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
    from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
    from convert.adapters.solidworks.Archive.Partition.CheckXmtAttrs import CheckXmtAttrs
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import ReadBodyTree
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import ReadOutputAtom
    cases = {case['name']: case for case in job['cases']}
    observations = []
    sources = {}
    for row in result['cases']:
        case = cases[row['name']]
        for state, file_name, checksum, expected in (
            ('baseline', 'Author/Baseline.SLDPRT', row['author']['baseline_sha256'], 'AnchorBoss'),
            ('renamed', 'Author/Renamed.SLDPRT', row['author']['renamed_sha256'], case['body_name']),
            ('reopened', 'Fresh/Reopened.SLDPRT', row['fresh']['reopened_sha256'], case['body_name'])):
            path = args.packet / 'Inspection' / row['name'] / file_name
            data = path.read_bytes()
            if digest(data) != checksum:
                raise ValueError('disclosed unicode save differs: ' + str(path))
            sources[str(path)] = checksum
            archive = SldprtArchive.from_bytes(data)
            link = ReadNativeLink(archive, 0)
            header = ReadHeaderGraph(archive.require('Contents/Config-0-ModelHeader'), 19000)
            config_data, config = WriteConfigMut(link.ConfigValue.RootValue, 19000, header)
            resolved_data, _ = WriteResolMut(link.ResolvedValue.RootsValue,
                link.ResolvedValue.ExtraFields, 19000, config.MapValue, link.ResolvedValue.ContextValue)
            if config_data != archive.require('Contents/Config-0') or resolved_data != archive.require(link.StreamName):
                raise ValueError('unicode archive string owners do not round trip exactly')
            model = link.ConfigValue.RootValue
            atom, = [item['o'] for item in model.FieldsValue['fd88']['atoms']]
            boss, = [value for value in link.ResolvedValue.RootsValue if value is not None
                     and value.ClassValue.NameValue == 'moExtrusion_c']
            if ReadOutputAtom(boss) is not atom:
                raise ValueError('unicode body output does not share the actual manager atom')
            payloads = DecodePartData(archive.require('Contents/Config-0-Partition'))
            if tuple(payload.kind for payload in payloads) != ('partition', 'deltas'):
                raise ValueError('unicode source has alternate kernel ownership')
            nodes, raw_chars = read_active(payloads[0].data)
            CheckXmtGraph(nodes)
            ReadXmtHistory(payloads[1].data, nodes)
            tree = ReadBodyTree(nodes)
            body = nodes[tree.BodyIndex]
            CheckXmtAttrs(nodes, body)
            attrs = ReadBodyAttrs(nodes, body)
            attr_rows = {}
            for name in ('SDL/TYSA_NAME', 'SDL/TYSA_UNAME', 'SWIMPLICITBODYNAME_ID_U', 'SW_INTERNAL_BODY_NAME'):
                attribute = attrs.get(name)
                if attribute is None:
                    attr_rows[name] = None
                    continue
                definition = nodes[attribute.Integer('definition')]
                values = []
                for index in attribute.Indexes('fields'):
                    if not index:
                        values.append(None)
                    elif nodes[index].KindValue == 98:
                        values.append({'kind': 98, **unicode_value(nodes[index].Indexes('values'))})
                    elif nodes[index].KindValue == 84:
                        raw = raw_chars[index, 'values']
                        decoded = {}
                        for codec in ('ascii', 'utf-8', 'cp1252'):
                            try:
                                decoded[codec] = raw.decode(codec)
                            except UnicodeError:
                                decoded[codec] = None
                        values.append({'kind': 84, 'raw_hex': raw.hex(), 'raw_bytes': len(raw),
                                       'diagnostic_decodings_only': decoded})
                    else:
                        values.append({'kind': nodes[index].KindValue})
                attr_rows[name] = {'type_id': definition.Integer('type_id'),
                    'field_types': definition.Indexes('fields'), 'values': values,
                    'actual_body_owner': attribute.Integer('owner') == body.IndexValue}
            atom_name = ReadNativeName(atom) if atom.FieldsValue['f18'] is not None else None
            observations.append({'case': row['name'], 'state': state, 'file_sha256': checksum,
                'expected_native_body_name': expected, 'atom_name': atom_name,
                'atom_name_derived': atom.FieldsValue['f18c'],
                'atom_id': atom.FieldsValue['f140'], 'base_feature_id': atom.FieldsValue['f12c'],
                'last_modifying_feature_id': atom.FieldsValue['f130'], 'boss_id': boss.FieldsValue['f08'],
                'body_transmit_index': body.IndexValue, 'attributes': attr_rows,
                'complete_body_graph': True, 'output_atom_alias': True,
                'config_roundtrip': True, 'resolved_roundtrip': True,
                'active_payload_sha256': payloads[0].sha256,
                'character_bytes_preserved_without_codec_claim': True})
    immutable = all(digest(Path(path).read_bytes()) == checksum for path, checksum in sources.items())
    output = {'schema': 'kit.sw2026.unicode-body-owner-correlation.v1',
        'packet_sha256': digest(job_data), 'native_result_sha256': digest(result_data),
        'observations': observations, 'sources_immutable': immutable,
        'heldout_inputs_read': 0, 'sdk_changed': False, 'public_reader_verification': False,
        'scope': 'metadata-only full typed archive and raw-character kernel ownership correlation'}
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(dumps(output, indent=2, sort_keys=True) + '\n')
    if not immutable:
        raise RuntimeError('unicode source changed during observation')


if __name__ == '__main__':
    main()
