import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser()
    for name in ('method', 'guest-discovery', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--method-sha256', required=True)
    args = parser.parse_args()
    method_path = args.method.resolve(strict=True)
    root = method_path.parent
    sys.path[:0] = [str(root / 'GuestTools'), str(root / 'CodeRoot/src'), str(root / 'CodeRoot/re/tooling/sw2026')]
    from VerifyPerpendicularFreeze import verify
    from ComparePerpendicularRuntimes import normalized, differences
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    _, method = verify(method_path, args.method_sha256)
    discovery = load(args.guest_discovery)
    require(discovery['passed'] and discovery['method_sha256'] == args.method_sha256
            and discovery['heldout_inputs_read'] == 0 and not discovery['permits_hidden_release'],
            'only disclosed runtime discovery can be compared before hidden release')
    guest_folder = args.guest_discovery.resolve(strict=True).parent / 'A'
    fixture = load(root / 'Inputs/G01RegistryInput.json')
    names = {'parent': fixture['document']['metadata']['name'] + '.SLDASM',
             'child': fixture['document']['assembly']['documents']['$tuple'][0]['document']['metadata']['name'] + '.SLDPRT'}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for role, name in names.items():
        host_file, guest_file = root / 'Inputs/HostGenerated' / name, guest_folder / name
        require(digest(guest_file) == discovery['files'][role]['sha256'], 'the disclosed guest artifact changed')
        archives = [SldprtArchive.from_bytes(path.read_bytes()) for path in (host_file, guest_file)]
        require(tuple(archives[0].streams) == tuple(archives[1].streams), 'disclosed runtime stream topology differs')
        streams = []
        allowed = {'Contents/Config-0', 'Contents/Config-0-MatesList'} if role == 'parent' else {'Contents/Config-0'}
        for stream, before in archives[0].streams.items():
            after = archives[1].require(stream)
            require(len(before) == len(after), 'disclosed runtime logical stream length differs')
            require(before == after or stream in allowed, 'a stream outside the predeclared arithmetic owners differs')
            streams.append({'stream': stream, 'bytes': len(before), 'exact_equal': before == after,
                            'host_sha256': sha256(before).hexdigest(), 'guest_sha256': sha256(after).hexdigest(),
                            'changed_byte_count': sum(a != b for a, b in zip(before, after, strict=True))})
        graphs = []
        for label, archive in zip(('host', 'guest'), archives, strict=True):
            linked = ReadNativeLink(archive, 0)
            graph = {'configuration': linked.ConfigValue, 'resolved': linked.ResolvedValue}
            if role == 'parent':
                graph['mates'] = ReadMatesMut(archive.require('Contents/Config-0-MatesList'), linked.ResolvedValue)
            graphs.append(normalized(graph))
            (output / (role + '-' + label + '-graph.json')).write_text(json.dumps(graphs[-1], indent=2, sort_keys=True) + '\n')
        delta = differences(*graphs)
        counts = {'moView_c': 0, 'moPlaneRef_w': 0}
        for value in delta:
            owner = value['owner']
            relative = value['path'][len(owner['path']):]
            if owner['class'] == 'moView_c':
                require(relative in ('/fields/f368/f08/m0', '/fields/f368/f08/m4', '/fields/f368/f08/m8')
                        and value['ulp_distance'] <= 2 and value['absolute_delta'] <= 1e-29,
                        'a disclosed camera difference exceeds the independently explained runtime arithmetic')
            else:
                require(role == 'parent' and owner['class'] == 'moPlaneRef_w'
                        and relative == '/fields/f100/f60' and value['ulp_distance'] <= 2
                        and value['absolute_delta'] <= 2e-18,
                        'a disclosed reference difference exceeds the independently explained inverse/sum arithmetic')
            counts[owner['class']] += 1
        require(counts['moView_c'] <= 8 and counts['moPlaneRef_w'] <= (1 if role == 'parent' else 0),
                'more disclosed runtime owners differ than the predeclared ordinary profile')
        records.append({'role': role, 'host_file_sha256': digest(host_file), 'guest_file_sha256': digest(guest_file),
                        'logical_streams': streams, 'derived_double_differences': delta,
                        'all_nonfloating_typed_fields_and_aliases_equal': True, 'within_predeclared_scope': True})
    verify(method_path, args.method_sha256)
    receipt = {'schema': 'kit.sw2026.public-perpendicular-disclosed-runtime-comparison.v1',
               'method_sha256': args.method_sha256, 'guest_discovery_sha256': digest(args.guest_discovery),
               'records': records, 'all_nonfloating_typed_fields_and_aliases_equal': True,
               'all_other_logical_streams_equal': True, 'stream_lengths_and_topology_equal': True,
               'differences_within_predeclared_runtime_scope': True, 'heldout_inputs_read': 0,
               'native_processes_started': 0, 'writer_math_changed': False, 'byte_patch_added': False,
               'basis': 'unchanged source; predeclared camera normalization and inverse-plane floating sum owners only'}
    data = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    (output / 'Comparison.json').write_bytes(data)
    print(json.dumps({'passed': True, 'comparison_sha256': sha256(data).hexdigest(),
                      'double_difference_counts': {row['role']: len(row['derived_double_differences']) for row in records},
                      'heldout_inputs_read': 0, 'native_processes_started': 0}))


if __name__ == '__main__':
    main()
