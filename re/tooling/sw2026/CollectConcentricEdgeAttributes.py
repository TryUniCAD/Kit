from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from struct import unpack


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    for name in ('support', 'model', 'geometry', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'choose an unused native attribute receipt')
    require(sha256(args.support.read_bytes()).hexdigest() == '55edce424c2359f7b126f8cfa72516ae6b7924b404e3bef2b67a5746c3398b8d', 'pinned PE reader changed')
    spec = importlib.util.spec_from_file_location('concentric_edge_native', args.support)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.Image(args.model)
    geometry = module.Image(args.geometry)
    identities = {'model': module.module(model, '569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e'),
                  'geometry': module.module(geometry, '77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594')}
    functions = {}
    entries = [('make_sketch_edge', model, 0x4BA9E830, 'f1891bc1f1ddacb9aa6f1f5da38480a4e81242299f968356214efc29fe21746d'),
               ('surface_assignment', model, 0x4B788170, 'b1481219e76a89972c9b5891c5863dbf83efc2fcbe6297fe1ed236a57b41e60f'),
               ('propagate_edge_ids', geometry, 0x439BAC50, 'be33f2152a5dd81d14dd5743a1ee3556b78de4fa266ec1ae4ed31a15240e46dd'),
               ('assign_id_runtime', geometry, 0x43E775C0, 'e617b35067c469bb9382043ed465c450b0f93d504b642f2c6f3dcb1451dce19e'),
               ('get_id_runtime', geometry, 0x43E843B0, '1120a466c49395f1a91743ff86eeefd195357dfbe4a48ce966b84619070a175e')]
    for name, image, address, expected in entries:
        row = image.function(address)
        require(row.get('start_va') == hex(address) and row.get('code_sha256') == expected, 'native function identity changed: ' + name)
        functions[name] = row
    start, end = 0x439BBFD0, 0x439BC0BD
    fragments = [(geometry.base + a, geometry.base + b, u) for a, b, u in geometry.functions
                 if geometry.base + a < end and geometry.base + b > start]
    require(len(fragments) == 5 and fragments[0][0] == start and fragments[-1][1] == end,
            'fragmented pointer-copy native coverage changed')
    require(all(a[1] == b[0] for a, b in zip(fragments, fragments[1:])), 'native body fragments are not contiguous')
    body = geometry.bytes(start, end)
    require(body[-1] == 0xC3 and sha256(body).hexdigest() == '74c75db49342c7ebf974eda91d719cf15e0d7674dbe3acd166bd8bceaa0e41fd', 'native pointer-copy body changed')
    functions['propagate_edge_pointer_values'] = {'start_va': hex(start), 'end_va_exclusive': hex(end),
        'code_sha256': sha256(body).hexdigest(), 'unwind_fragments':
        [{'start_va': hex(a), 'end_va_exclusive': hex(b), 'unwind_rva': hex(u)} for a, b, u in fragments]}
    edges = []
    for image, site, target, kind in [(geometry, 0x439BAC7F, start, 'call'),
                                       (geometry, 0x439A8AF0, 0x43E775C0, 'jump'),
                                       (geometry, 0x439AE0F0, 0x43E843B0, 'jump')]:
        word = image.bytes(site, site + 5)
        require(word[0] == (0xE8 if kind == 'call' else 0xE9) and site + 5 + unpack('<i', word[1:])[0] == target, 'native direct edge changed')
        edges.append({'site_va': hex(site), 'target_va': hex(target), 'kind': kind})
    indirect = model.bytes(0x4BA9E8ED, 0x4BA9E8F3)
    require(indirect[:2] == b'\xff\x15' and 0x4BA9E8F3 + unpack('<i', indirect[2:])[0] == 0x4CD38618, 'sketch pointer publication call changed')
    require('PEAX@Z' in model.imports[0x4CD38618]['symbol'], 'native pointer attribute signature changed')
    result = {'schema': 'kit.sw2026.concentric-edge-attribute-bindings.v1', 'modules': identities,
              'functions': functions, 'direct_edges': edges,
              'sketch_publication': {'flag_mask': 1, 'actual_entity_slot': '0x378', 'kernel_edge_slot': '0x88',
                  'entity_pointer_receiver_call_va': '0x4ba9e8d7', 'attribute_iat_va': '0x4cd36f88',
                  'attribute_import': model.imports[0x4CD36F88], 'make_attribute_call_va': '0x4ba9e8ed',
                  'make_attribute_import': model.imports[0x4CD38618], 'payload_domain': 'actual sgEnt pointer'},
              'propagation': {'source_attribute_va': '0x44165db8', 'destination_attribute_va': '0x44165df0',
                  'one_pointer_get_va': '0x439bc043', 'one_pointer_store_va': '0x439bc056',
                  'three_pointer_store_va': '0x439bc070', 'payload_converted_to_permanent_marker_here': False},
              'geometry_backend': {hex(a): geometry.imports[a] for a in (0x43F5A638, 0x43F5A648)},
              'limits': {'sketch_permanent_marker_publication_end_to_end': 'unresolved',
                         'fresh_kernel_face_numbering': 'unresolved', 'optional_axis_constructor': 'unresolved'},
              'support_sha256': sha256(args.support.read_bytes()).hexdigest(),
              'tool_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'native_processes_started': 0, 'hidden_inputs_read': 0, 'writer_outputs': 0, 'hopper_sessions_opened': 0}
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'passed': True, 'sha256': sha256(args.output.read_bytes()).hexdigest(), 'function_closures': len(functions)}, sort_keys=True))


if __name__ == '__main__':
    main()
