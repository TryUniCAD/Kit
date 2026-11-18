import argparse
from base64 import b64decode
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def normalized(value):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

    seen = {}
    def visit(item):
        if isinstance(item, ArchiveNode):
            if id(item) in seen:
                return {'node_ref': seen[id(item)]}
            number = len(seen)
            seen[id(item)] = number
            return {'node_id': number, 'class': item.ClassValue.NameValue,
                    'schema': item.ClassValue.SchemaValue, 'fields': visit(item.FieldsValue)}
        if is_dataclass(item):
            return {'record': type(item).__name__, 'values': {field.name: visit(getattr(item, field.name)) for field in fields(item)}}
        if isinstance(item, Mapping):
            return {str(key): visit(data) for key, data in sorted(item.items(), key=lambda pair: str(pair[0]))}
        if isinstance(item, (list, tuple)):
            return [visit(data) for data in item]
        if type(item) is float:
            return {'ieee_double': item.hex()}
        if isinstance(item, bytes):
            return {'byte_count': len(item), 'bytes_sha256': digest(item)}
        require(item is None or type(item) in (int, bool, str), 'the typed graph contains an unnormalized owner')
        return item
    return visit(value)


def differences(first, second):
    result = []
    def visit(left, right, path, owner):
        if left == right:
            return
        require(type(left) is type(right), 'runtime graph structure or typed value kind differs')
        if isinstance(left, dict):
            require(left.keys() == right.keys(), 'runtime graph field ownership differs')
            if 'class' in left:
                require(left['class'] == right['class'], 'runtime graph native class differs')
                owner = {'class': left['class'], 'path': path, 'node_id': left['node_id']}
            if set(left) == {'ieee_double'}:
                before, after = float.fromhex(left['ieee_double']), float.fromhex(right['ieee_double'])
                ordered = lambda value: (1 << 63) - struct.unpack('>Q', struct.pack('>d', value))[0] if value < 0 else (1 << 63) + struct.unpack('>Q', struct.pack('>d', value))[0]
                result.append({'path': path, 'owner': owner, 'host_hex': left['ieee_double'], 'guest_hex': right['ieee_double'],
                               'host_value': before, 'guest_value': after, 'absolute_delta': abs(before-after),
                               'ulp_distance': abs(ordered(before)-ordered(after))})
                return
            for key in left:
                visit(left[key], right[key], path + '/' + key, owner)
        elif isinstance(left, list):
            require(len(left) == len(right), 'runtime graph array length differs')
            for index, (before, after) in enumerate(zip(left, right, strict=True)):
                visit(before, after, path + '/' + str(index), owner)
        else:
            raise ValueError('a nonfloating typed field differs: ' + path)
    visit(first, second, '', None)
    return result


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'host-worker', 'guest-worker', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    sys.path.insert(0, str(root / 'src'))
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    host, guest = (json.loads(path.read_bytes()) for path in (args.host_worker, args.guest_worker))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    require(host['passed'] and guest['passed'] and host['runtime_input_file_reads'] == guest['runtime_input_file_reads'] == 0
            and host['sdk_runtime_research_imports'] == guest['sdk_runtime_research_imports'] == 0,
            'the runtime comparison requires two successful generated source-only bundles')
    records = []
    for role in ('assembly', 'child'):
        a, b = (value[role] for value in (host, guest))
        require(a['stream_order'] == b['stream_order'], 'runtime stream topology differs')
        logical = []
        for name in a['stream_order']:
            before, after = (b64decode(value['streams'][name]['data'], validate=True) for value in (a, b))
            require(len(before) == len(after), 'runtime logical stream length differs')
            logical.append({'stream': name, 'bytes': len(before), 'exact_equal': before == after,
                            'host_sha256': digest(before), 'guest_sha256': digest(after),
                            'differing_byte_count': sum(left != right for left, right in zip(before, after, strict=True))})
        graphs = []
        for label, artifact in (('host', a), ('guest', b)):
            archive = SldprtArchive.from_bytes(b64decode(artifact['blob'], validate=True))
            link = ReadNativeLink(archive, 0)
            graph = {'configuration': link.ConfigValue, 'resolved': link.ResolvedValue}
            if role == 'assembly':
                graph['mates'] = ReadMatesMut(archive.require('Contents/Config-0-MatesList'), link.ResolvedValue)
            value = normalized(graph)
            (output / (role + '-' + label + '-graph.json')).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
            graphs.append(value)
        delta = differences(*graphs)
        records.append({'role': role, 'host_file_sha256': a['sha256'], 'guest_file_sha256': b['sha256'],
                        'host_file_bytes': a['bytes'], 'guest_file_bytes': b['bytes'], 'logical_streams': logical,
                        'all_nonfloating_typed_fields_and_aliases_equal': True, 'derived_double_differences': delta})
    receipt = {'schema': 'kit.sw2026.perpendicular-disclosed-runtime-typed-comparison.v1',
               'host_worker_sha256': digest(args.host_worker.read_bytes()), 'guest_worker_sha256': digest(args.guest_worker.read_bytes()),
               'source_root': str(root), 'records': records, 'heldout_inputs_read': 0, 'native_processes_started': 0,
               'benign_classification_requires_independent_formula_mapping': True, 'acceptance_gate_changed': False}
    data = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    (output / 'RuntimeComparison.json').write_bytes(data)
    print(json.dumps({'result_sha256': digest(data), 'typed_double_counts': {row['role']: len(row['derived_double_differences']) for row in records},
                      'all_nonfloating_typed_fields_and_aliases_equal': True, 'heldout_inputs_read': 0, 'native_processes_started': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
