from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from sys import path as module_path


def require(value, message):
    if not value:
        raise ValueError(message)


def source_snapshot(root):
    paths = tuple((root / 'src').rglob('*.py')) + tuple(root / relative for relative in (
        're/tooling/sw2026/para/Partition.py', 're/tooling/sw2026/para/Schema.py',
        're/tooling/sw2026/builders/EmptyPartition.py'))
    return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def chain(nodes, start, kind, next_key='next', previous_key='previous', owner=None):
    result = []
    previous = 0
    while start:
        require(start not in result and start in nodes, 'cycle or missing node')
        node = nodes[start]
        require(node.kind == kind, 'wrong chain member class')
        require(node.fields[previous_key] == previous, 'nonreciprocal previous link')
        if owner is not None:
            require(node.fields['owner'] == owner, 'wrong chain owner')
        result.append(start)
        previous, start = start, node.fields[next_key]
    return tuple(result)


def attribute(nodes, node):
    definition = nodes[node.fields['definition']]
    require(definition.kind == 80, 'attribute has no typed definition')
    identity = nodes[definition.fields['identifier']]
    require(identity.kind == 79, 'attribute has no typed identifier')
    types = definition.fields['fields']
    refs = node.fields['fields']
    require(len(types) == len(refs), 'attribute field arity differs')
    values = []
    for kind, ref in zip(types, refs, strict=True):
        if not ref:
            values.append(None)
            continue
        require(kind in {1, 2, 3, 10}, 'unrecognized attribute value type')
        item = nodes[ref]
        require(item.kind == {1: 82, 2: 83, 3: 84, 10: 98}[kind],
                'attribute value differs from definition type')
        values.append(item.fields['values'])
    return {'index': node.index, 'owner': node.fields['owner'],
            'definition_index': definition.index, 'identifier_index': identity.index,
            'identifier': identity.fields['string'], 'type_id': definition.fields['type_id'],
            'field_types': types, 'field_refs': refs, 'values': values}


def inspect_body(partition, body_index):
    nodes = {node.index: node for node in partition.nodes}
    body = nodes[body_index]
    attrs = chain(nodes, body.fields['attributes_features'], 81, owner=body_index)
    require(set(attrs) == {node.index for node in partition.nodes
                           if node.kind == 81 and node.fields['owner'] == body_index},
            'body owner list omits an active attribute')
    attr_values = tuple(attribute(nodes, nodes[index]) for index in attrs)
    require(len({row['identifier'] for row in attr_values}) == len(attr_values),
            'ambiguous duplicate body attributes')
    by_name = {row['identifier']: row for row in attr_values}
    explicit = by_name.get('SDL/TYSA_NAME')
    if explicit is not None:
        require(explicit['type_id'] == 8017 and explicit['field_types'] == (3,)
                and len(explicit['values']) == 1 and type(explicit['values'][0]) is str,
                'explicit saved body-name shape is outside the disclosed profile')
        require(explicit['values'][0].isascii(), 'non-ASCII body name not qualified')
    unicode_name = by_name.get('SDL/TYSA_UNAME')
    regions = []
    current = body.fields['region']
    previous = 0
    while current:
        require(current not in regions and current in nodes, 'region cycle or missing node')
        region = nodes[current]
        require(region.kind == 19 and region.fields['body'] == body_index
                and region.fields['previous'] == previous, 'region ownership differs')
        regions.append(current)
        previous, current = current, region.fields['next']
    solid_regions = [index for index in regions if nodes[index].fields['type'] == 'S']
    void_regions = [index for index in regions if nodes[index].fields['type'] == 'V']
    require(len(regions) == 2 and len(solid_regions) == len(void_regions) == 1,
            'ordinary solid must own one solid and one void region')
    solid = nodes[solid_regions[0]]
    void = nodes[void_regions[0]]
    require(body.fields['shell'] == solid.fields['shell'], 'body shell is not the solid shell')
    shell = nodes[solid.fields['shell']]
    front = nodes[void.fields['shell']]
    require(shell.kind == front.kind == 13 and shell.fields['body'] == body_index
            and front.fields['body'] == 0
            and shell.fields['region'] == solid.index and front.fields['region'] == void.index,
            'solid and void shell attachments differ')
    faces = chain(nodes, shell.fields['face'], 14)
    front_faces = chain(nodes, front.fields['front_face'], 14,
                        next_key='next_front', previous_key='previous_front')
    require(set(faces) == set(front_faces), 'solid and void face inventories differ')
    loops, fins, edges, vertices, surfaces, curves, points = set(), set(), set(), set(), set(), set(), set()
    for face_index in faces:
        face = nodes[face_index].fields
        require(face['shell'] == shell.index and face['front_shell'] == front.index,
                'face has a foreign body shell')
        surfaces.add(face['surface'])
        loop_index = face['loop']
        while loop_index:
            require(loop_index not in loops, 'loop has multiple face owners')
            loop = nodes[loop_index]
            require(loop.kind == 15 and loop.fields['face'] == face_index, 'loop has a foreign face')
            loops.add(loop_index)
            first = loop.fields['halfedge']
            current = first
            while current not in fins:
                fin = nodes[current]
                require(fin.kind == 17 and fin.fields['loop'] == loop_index, 'fin has a foreign loop')
                mate = nodes[fin.fields['other']]
                following = nodes[fin.fields['forward']]
                require(mate.kind == following.kind == 17 and mate.fields['other'] == current
                        and following.fields['backward'] == current
                        and mate.fields['edge'] == fin.fields['edge'], 'fin links differ')
                fins.add(current)
                edges.add(fin.fields['edge'])
                vertices.add(fin.fields['vertex'])
                current = fin.fields['forward']
            require(current == first, 'fin loop shares another ring')
            loop_index = loop.fields['next']
    for index in edges:
        edge = nodes[index]
        require(edge.kind == 16, 'edge reference is not typed')
        curves.add(edge.fields['curve'])
    for index in vertices:
        vertex = nodes[index]
        require(vertex.kind == 18, 'vertex reference is not typed')
        points.add(vertex.fields['point'])
    topology = {'faces': faces, 'loops': sorted(loops), 'fins': sorted(fins), 'edges': sorted(edges),
                'vertices': sorted(vertices), 'surfaces': sorted(surfaces), 'curves': sorted(curves),
                'points': sorted(points)}
    return {'body_index': body_index, 'body_type': body.fields['body_type'],
            'owner_world': body.fields['owner'], 'attributes': attr_values,
            'explicit_label': explicit['values'][0] if explicit is not None else None,
            'unicode_explicit_present': unicode_name is not None,
            'implicit_label_attribute': by_name.get('SWIMPLICITBODYNAME_ID_U'),
            'internal_name_attribute': by_name.get('SW_INTERNAL_BODY_NAME'),
            'regions': regions, 'solid_shell': shell.index, 'void_shell': front.index,
            'solid_shell_body': shell.fields['body'], 'void_shell_body': front.fields['body'],
            'topology': topology,
            'legacy_scanner_face_ids': [index + 1 for index in faces],
            'legacy_scanner_edge_ids': [index + 1 for index in sorted(edges)],
            'legacy_scanner_vertex_ids': [index + 1 for index in sorted(vertices)]}


def inspect_file(path, expected, archive_class, read_partition, frame_payloads, write_payloads, read_link):
    from convert.Geometry.Parasolid import DecodePartData, HasParaPayload
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected['file_sha256'], 'locked source hash differs')
    archive = archive_class.from_bytes(data, path)
    link = read_link(archive, 0)
    stream_name = link.ConfigName + '-Partition'
    stream = archive.require(stream_name)
    partition = read_partition(stream)
    require(frame_payloads(write_payloads(partition)) == stream, 'typed partition roundtrip differs')
    nodes = {node.index: node for node in partition.nodes}
    world = nodes[1]
    definitions = []
    index = world.fields['attrib_def']
    while index:
        require(index not in definitions and nodes[index].kind == 80, 'attribute definition cycle or wrong class')
        definitions.append(index)
        index = nodes[index].fields['next']
    require(set(definitions) == {node.index for node in partition.nodes if node.kind == 80},
            'WORLD definition registry is incomplete')
    attr_heads = {}
    for node in partition.nodes:
        if node.kind != 81:
            continue
        row = node.fields
        require(row['definition'] in definitions, 'attribute is not registered in WORLD')
        if not row['previous_of_type']:
            require(row['definition'] not in attr_heads, 'per-definition chain has multiple heads')
            attr_heads[row['definition']] = node.index
        for previous, following, owner in (('previous', 'next', 'owner'),
                                           ('previous_of_type', 'next_of_type', 'definition')):
            if neighbor_id := row[following]:
                neighbor = nodes[neighbor_id]
                require(neighbor.kind == 81 and neighbor.fields[previous] == node.index
                        and neighbor.fields[owner] == row[owner], 'attribute chain is nonreciprocal')
    body_indices = chain(nodes, world.fields['body'], 12, owner=1)
    require(set(body_indices) == {node.index for node in partition.nodes if node.kind == 12},
            'WORLD body chain omits an active body')
    require(len(body_indices) == 1, 'this disclosed profile requires one body')
    body_list = nodes[nodes[body_indices[0]].fields['attribute_chains']]
    block = nodes[body_list.fields['list_block']]
    count = block.fields['n_entries']
    require(body_list.kind == 70 and block.kind == 74 and body_list.fields['owner'] == body_indices[0]
            and body_list.fields['finger_block'] == block.index
            and count == body_list.fields['list_length'] == len(attr_heads)
            and body_list.fields['block_length'] == len(block.fields['entries'])
            and set(block.fields['entries'][:count]) == set(attr_heads.values())
            and not any(block.fields['entries'][count:]), 'body per-definition index is inconsistent')
    bodies = [inspect_body(partition, index) for index in body_indices]
    require(bodies[0]['explicit_label'] == (expected.get('body_name_attribute') or {}).get('value'),
            'body label differs from disclosed archive evidence')
    for key, kind in [('faces', 14), ('loops', 15), ('fins', 17), ('edges', 16), ('vertices', 18),
                      ('surfaces', 50), ('curves', 30), ('points', 29)]:
        require(set(bodies[0]['topology'][key]) == {node.index for node in partition.nodes if node.kind == kind},
                'body topology does not exhaust active ' + key)
    entries = {id(entry.EntryValue): entry.EntryValue for entry in link.ResolvedValue.MapValue.EntriesValue}
    atoms = [node for node in entries.values()
             if getattr(getattr(node, 'ClassValue', None), 'NameValue', '') == 'moAtom_c']
    atom_rows = []
    for atom in atoms:
        row = {key: atom.FieldsValue[key] for key in ('f140','f130','f12c','f180','f1b0','f19c','body_kind','f18c')}
        holder = atom.FieldsValue['f18']
        require(holder is None or holder.ClassValue.NameValue == 'moNodeName_c', 'atom name has a foreign holder')
        row['name_holder_class'] = holder.ClassValue.NameValue if holder is not None else None
        row['authored_name'] = holder.FieldsValue['f08'] if holder is not None else None
        atom_rows.append(row)
    extrusions = [node for node in link.ResolvedValue.RootsValue
                  if node.ClassValue.NameValue == 'moExtrusion_c']
    require(len(atoms) == len(extrusions) == 1, 'single actual body/feature archive owner is not unique')
    body_attrs = {row['identifier']: row for row in bodies[0]['attributes']}
    atom = atom_rows[0]
    require(atom['f180'] == atom['f1b0'] == body_attrs['BODY_MATCH']['values'][0][0]
            and atom['f140'] == body_attrs['ATOM_ID_2001']['values'][1][0]
            and atom['f12c'] == atom['f130'] == extrusions[0].FieldsValue['f08']
            == body_attrs['LAST_BODY_MODIFYING_FEATURE_ID']['values'][1][0],
            'archive atom/body/last feature identities disagree')
    label = bodies[0]['explicit_label']
    require(atom['authored_name'] == label and atom['f18c'] == int(label is None),
            'archive authored name or derived-name flag differs from the disclosed native state')
    implicit = bodies[0]['implicit_label_attribute']
    require(implicit is not None and implicit['field_types'] == (10, 10)
            and implicit['values'][1] is None, 'implicit name has an unqualified value shape')
    implicit_label = ''.join(chr(code) for code in implicit['values'][0])
    if label is not None:
        require(implicit_label == label, 'explicit, implicit and authored atom names differ')
    payload_roles = [{'name': record.name, 'bytes': len(record.data),
                      'payloads': [{'kind': payload.kind, 'schema': payload.schema,
                                    'sha256': payload.sha256, 'bytes': len(payload.data)}
                                   for payload in DecodePartData(record.data, record.name)]}
                     for record in archive.records if HasParaPayload(record.data)]
    return {'file_sha256': expected['file_sha256'], 'file_bytes': len(data),
            'stream': stream_name, 'stream_sha256': sha256(stream).hexdigest(),
            'stream_bytes': len(stream), 'archive_version': link.ConfigValue.VersionValue,
            'model_class': link.ConfigValue.RootValue.ClassValue.NameValue,
            'typed_partition_roundtrip_exact': True,
            'active_counts': dict(Counter(str(node.kind) for node in partition.nodes)),
            'active_world_id': world.fields['current_id'], 'partition_roles': payload_roles,
            'world_definition_count': len(definitions), 'body_attribute_chain_count': count,
            'bodies': bodies, 'atoms': atom_rows,
            'actual_final_feature_id': extrusions[0].FieldsValue['f08'],
            'source_immutable': sha256(path.read_bytes()).hexdigest() == expected['file_sha256']}


def main():
    parser = ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--receipt-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--closure-output', type=Path, required=True)
    args = parser.parse_args()
    before_sources = source_snapshot(args.root)
    module_path[:0] = [str(args.root / 'src'), str(args.root / 're/tooling/sw2026')]
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from para.Partition import frame_payloads, read_partition, write_payloads
    receipt_data = args.receipt.read_bytes()
    require(sha256(receipt_data).hexdigest() == args.receipt_sha256, 'receipt hash differs')
    receipt = loads(receipt_data)
    result = {'schema': 'kit.sw2026.named-body-owner-observation.v1',
              'operation': 'offline typed archive observation, no public product verification',
              'receipt_sha256': args.receipt_sha256, 'cases': [], 'hidden_sources_read': 0,
              'writer_outputs': 0, 'vm_calls': 0, 'public_sdk_reads': 0}
    for row in receipt['cases']:
        for mode in ('baseline', 'renamed'):
            path = args.sources / 'Inspection' / row['case'] / 'Author' / (mode.title() + '.SLDPRT')
            result['cases'].append({'case': row['case'], 'state': mode,
                                    **inspect_file(path, row[mode], SldprtArchive, read_partition,
                                                   frame_payloads, write_payloads, ReadNativeLink)})
    require(source_snapshot(args.root) == before_sources, 'source closure changed during observation')
    closure = {'schema': 'kit.sw2026.named-body-owner-sources.v1', 'files': before_sources,
               'tool_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    closure_data = dumps(closure, indent=2, sort_keys=True) + '\n'
    result['source_closure_sha256'] = sha256(closure_data.encode()).hexdigest()
    result['source_closure_files'] = len(before_sources)
    result['tool_sha256'] = closure['tool_sha256']
    with args.closure_output.open('x', encoding='utf-8', newline='\n') as output:
        output.write(closure_data)
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        output.write(dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
