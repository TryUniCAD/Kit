from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from struct import unpack


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--support', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'choose a new exact-build evidence receipt')
    support_hash = sha256(args.support.read_bytes()).hexdigest()
    require(support_hash == '55edce424c2359f7b126f8cfa72516ae6b7924b404e3bef2b67a5746c3398b8d',
            'shared original PE evidence helper changed')
    spec = importlib.util.spec_from_file_location('concentric_identity_pe', args.support)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    image = module.Image(args.image)
    identity = module.module(image, '569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e')

    def leaf(address, expected):
        body = image.bytes(address, address + 4)
        require(body[0] == 0x8B and body[1] == 0x41 and body[3] == 0xC3,
                'declared leaf is not a direct x64 receiver-relative integer load and return')
        require(body[2] == expected, 'native field getter changed its receiver displacement')
        return {'va': hex(address), 'bytes': 4, 'field_displacement': hex(body[2]),
                'code_sha256': sha256(body).hexdigest()}

    def call(address, target):
        data = image.bytes(address, address + 5)
        require(data[0] == 0xE8, 'declared edge is not a direct native call')
        observed = address + 5 + unpack('<i', data[1:])[0]
        require(observed == target, 'declared exact-build native call target changed')
        return {'site_va': hex(address), 'target_va': hex(observed)}

    def wide(address):
        data = image.bytes(address, address + 64)
        end = next(index for index in range(0, len(data), 2) if data[index:index + 2] == b'\0\0')
        return data[:end].decode('utf-16-le')

    entries = {
        'faceted_constructor': 0x4B7E9C60,
        'faceted_default_constructor': 0x4B7E9DC0,
        'graphics_reference': 0x4B7FA3D0,
        'facet_tessellation_lookup': 0x4B7FF2C0,
        'make_surface_id': 0x4C6D2B00,
        'surface_id_constructor': 0x4C6C2870,
        'from_edge_surface_assignment': 0x4B788170,
        'feature_reference_keeper': 0x4BB5D2A0,
        'actual_arc_runtime_factory': 0x4C5780D0,
        'actual_arc_handle_constructor': 0x4C55D940,
        'actual_arc_entity_receiver': 0x4C562F20,
        'permanent_marker': 0x4C5C7740,
        'surface_string': 0x4BA878B0,
        'surface_string_base': 0x4C6CE4A0,
        'multi_surface_string': 0x4BE98610,
    }
    functions = {name: image.function(address) for name, address in entries.items()}
    require(all(row.get('start_va') == hex(entries[name]) and 'end_va_exclusive' in row
                for name, row in functions.items()), 'whole native function closure is not exact')
    descriptor = 0x4DAFB0E8
    runtime_factory = image.unpack('Q', image.offset(descriptor + 16 - image.base))
    arc_vtable = 0x4D1C5AE8
    arc_entity = image.unpack('Q', image.offset(arc_vtable + 0x378 - image.base))
    surface_vtable = 0x4CF6AB10
    surface_string = image.unpack('Q', image.offset(surface_vtable + 0xA0 - image.base))
    require((runtime_factory, arc_entity, surface_string) == (0x4C5780D0, 0x4C562F20, 0x4BA878B0),
            'concrete native runtime descriptor or primary-table binding changed')
    getters = {
        'facet_face_node_id_f40': leaf(0x4B286570, 0x40),
        'facet_body_atom_id_f50': leaf(0x4B283940, 0x50),
        'facet_feature_id_f54': leaf(0x4B286690, 0x54),
        'actual_entity_permanent_marker_f08': leaf(0x4B283BA0, 0x08),
    }
    calls = [call(site, target) for site, target in (
        (0x4C5C780D, 0x4B283BA0), (0x4C5780FA, 0x4C55D940),
        (0x4C6D2B3E, 0x4C6C2870), (0x4C6C28A5, 0x4BB5D2A0),
        (0x4B7883F5, 0x4C6D2B00), (0x4B7FA622, 0x4B810770),
        (0x4B7FA672, 0x4BE98610), (0x4B7FA6EC, 0x4B7E9C60),
        (0x4BA878F1, 0x4C6CE4A0),
    )]
    formats = {'append_signed_entity': wide(0x4CF08D90), 'surface_separator': wide(0x4CDC6D08)}
    require(formats == {'append_signed_entity': '%s,%d', 'surface_separator': ', '},
            'ordinary native identity text format changed')
    result = {
        'schema': 'kit.sw2026.concentric-face-identity-native-bindings.v1',
        'module': identity, 'functions': functions, 'getters': getters, 'direct_call_edges': calls,
        'concrete_arc_binding': {'descriptor_va': hex(descriptor), 'factory_va': hex(runtime_factory),
                                 'primary_table_va': hex(arc_vtable), 'entity_slot': '0x378', 'target_va': hex(arc_entity)},
        'concrete_surface_binding': {'primary_table_va': hex(surface_vtable), 'text_slot': '0xa0', 'target_va': hex(surface_string)},
        'graphics_inputs': {hex(address): image.imports[address] for address in (0x4CD38788, 0x4CD380D8, 0x4CD37FE8, 0x4CD38000)},
        'surface_entity_store_va': '0x4c6c28d0', 'formats': formats,
        'claims': {'native_field_displacements': 'confirmed static',
                   'ordinary_surface_constructor_receives_actual_feature_and_unsigned_entity': 'confirmed static',
                   'marker_handle_receiver_selects_actual_arc': 'confirmed static',
                   'upstream_sketch_marker_to_kernel_from_edge_attribute': 'partial; not traced end to end',
                   'kernel_face_node_number_from_fresh_parametric_model': 'unresolved',
                   'facet_omission_or_minus_one_recovery': 'unmeasured'},
        'source_only': True, 'vendor_runtime_executed': False, 'hidden_inputs_read': 0,
        'writer_outputs': 0, 'hopper_sessions_opened': 0,
        'support_sha256': support_hash, 'script_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'sha256': sha256(args.output.read_bytes()).hexdigest(), 'functions': len(functions)}, sort_keys=True))


if __name__ == '__main__':
    main()
