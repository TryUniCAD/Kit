from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

PIN = '569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e'
BOUNDS = {
    'selected_regen': (0x4B706F00, 0x4B707317, '2781cb199fe88a53351db50ca3219048c4d47a3ffa74888e58314181be67f4a4'),
    'count_more_than_n_solids': (0x4BCF7EB0, 0x4BCF8105, 'bab9e9fc05b767b325d747b1b794e7ced8a1cc5746ce432a4de75c9c388164f2'),
    'selected_body_constructor': (0x4B7E8980, 0x4B7E8E32, '75ff8caaa1e2563fce09b057422cba3d9e96260be5087c0f74175853c57acd12'),
    'component_atom_base_constructor': (0x4B2786C0, 0x4B2787AF, 'f64697feba8bef0885c2a7650d69d4efe9d0b2de2ed28c928b8e5ef311ebb92f'),
    'component_reference_constructor': (0x4B7E8250, 0x4B7E8386, 'd22db22d6408ae1b4cb6638678e1fe5ccbbbd260a2ba28555042068e2d3b7f6c'),
    'base_atom_walk': (0x4BCF2F80, 0x4BCF3170, '13cc81fee4e41b65fb74cc17336ee1e26c36e5349aa8a490f8d144a6c806a22f'),
    'selected_body_serializer': (0x4BBA4390, 0x4BBA46B7, 'ecfa22d8123b4b926cc1834d3e59919db33f14e6e979b2c88de0be3f7c1f1cac'),
    'atom_feature_serializer': (0x4BB0B0C0, 0x4BB0CD82, '73fc5118ed366b226491bdfd3b064c5c1a8bff8f74456bdcce47449cc24b41c3'),
    'body_merge': (0x4B70C7C0, 0x4B710CD7, 'bc1063f80e2b3fadb964d6b45975759a1e91112e3818aa177c01558043d2704c'),
}


def collect(path):
    payload = path.read_bytes()
    if sha256(payload).hexdigest() != PIN:
        raise ValueError('the original pinned 2026 SP05.2 model image is required')
    pe = pefile.PE(data=payload, fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXCEPTION']])
    base = pe.OPTIONAL_HEADER.ImageBase
    spans = {(base + e.struct.BeginAddress, base + e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION}
    engine = Cs(CS_ARCH_X86, CS_MODE_64)
    engine.detail = True
    instructions = {}
    ranges = {}
    for name, (start, end, digest) in BOUNDS.items():
        assert (start, end) in spans, (name, 'unwind range changed')
        raw = pe.get_data(start-base, end-start)
        assert sha256(raw).hexdigest() == digest, (name, 'native range changed')
        instructions[name] = {i.address: i for i in engine.disasm(raw, start)}
        ranges[name] = {'start': hex(start), 'end_exclusive': hex(end), 'bytes': len(raw), 'sha256': digest}

    def point(name, address, mnemonic, offset=None, value=None, target=None, register=None):
        item = instructions[name][address]
        assert item.mnemonic == mnemonic, (name, hex(address), mnemonic)
        if offset is not None:
            assert any(o.type == X86_OP_MEM and o.mem.disp == offset for o in item.operands)
        if value is not None:
            assert any(o.type == X86_OP_IMM and o.imm == value for o in item.operands)
        if target is not None:
            assert item.operands[0].type == X86_OP_IMM and item.operands[0].imm == target
        if register is not None:
            assert any(o.type == X86_OP_REG and item.reg_name(o.reg) == register for o in item.operands)
        return {'range': name, 'instruction': hex(address), **({'offset': hex(offset)} if offset is not None else {}), **({'constant': value} if value is not None else {}), **({'target': hex(target)} if target is not None else {})}

    checks = {
        'persisted_scope': point('selected_regen', 0x4B706FB5, 'cmp', 0x544),
        'separate_runtime_auto': point('selected_regen', 0x4B706FC2, 'cmp', 0x558),
        'selected_list_load': point('selected_regen', 0x4B706FD7, 'mov', 0x548),
        'absent_list_skips': point('selected_regen', 0x4B706FE1, 'je', target=0x4B70729E),
        'one_selected_wrapper': point('selected_regen', 0x4B706FE7, 'cmp', 0x10, value=1),
        'at_most_one_solid_guard': point('selected_regen', 0x4B70705B, 'call', target=0x4BCF7EB0),
        'count_actual_solids': point('count_more_than_n_solids', 0x4BCF8083, 'call'),
        'count_limit_is_strict': point('count_more_than_n_solids', 0x4BCF8091, 'jg', target=0x4BCF80F3),
        'one_regenerated_body': point('selected_regen', 0x4B7070AC, 'cmp', value=1),
        'empty_runtime_entity_cache': point('selected_regen', 0x4B7070E2, 'cmp', 0x78, value=0),
        'unit_component_virtual': point('selected_regen', 0x4B707106, 'call', 0x260),
        'actual_atom_id_match': point('selected_regen', 0x4B707111, 'cmp', 0x18),
        'chosen_body_append': point('selected_regen', 0x4B70711C, 'call'),
        'wrapper_actual_id': point('selected_body_constructor', 0x4B7E8A36, 'mov', 0x18, register='r13d'),
        'wrapper_original_id': point('selected_body_constructor', 0x4B7E8A3A, 'mov', 0x1C, register='r13d'),
        'actual_manager_atom_lookup': point('selected_body_constructor', 0x4B7E8A9B, 'call', target=0x4BCF2EA0),
        'lineage_requires_live_body': point('selected_body_constructor', 0x4B7E8BBD, 'cmp', 0x160, value=0),
        'base_owner_feature_id': point('selected_body_constructor', 0x4B7E8C0A, 'mov', 0x108),
        'base_walk': point('selected_body_constructor', 0x4B7E8D90, 'call', target=0x4BCF2F80),
        'lineage_reads_actual_atom_id': point('selected_body_constructor', 0x4B7E8DB8, 'mov', 0x140),
        'constructor_empty_face': point('component_atom_base_constructor', 0x4B278743, 'mov', 0xF0),
        'constructor_empty_cache_words': point('component_atom_base_constructor', 0x4B278751, 'mov', 0x100),
        'constructor_unresolved_base_id': point('component_atom_base_constructor', 0x4B278758, 'mov', 0x108, value=0xFFFFFFFF),
        'lineage_starts_with_actual_atom': point('base_atom_walk', 0x4BCF2FE8, 'call'),
        'base_feature_source': point('base_atom_walk', 0x4BCF2FEE, 'mov', 0x150),
        'first_feature_without_consumed_atoms': point('base_atom_walk', 0x4BCF303B, 'mov', 0x530),
        'selected_wrapper_written': point('atom_feature_serializer', 0x4BB0B8C2, 'lea', 0x548),
        'scope_written': point('atom_feature_serializer', 0x4BB0B8E2, 'mov', 0x544),
        'scope_loaded': point('atom_feature_serializer', 0x4BB0B8F1, 'lea', 0x544),
        'wire_face_cache_reset': point('selected_body_serializer', 0x4BBA444F, 'mov', 0x100),
        'wire_face_cache_read_guard': point('selected_body_serializer', 0x4BBA4494, 'mov', 0xF8),
        'merge_reaches_selected_lookup': point('body_merge', 0x4B70CB1B, 'call', target=0x4B706F00),
        'merge_auto_snapshot': point('body_merge', 0x4B70E5B4, 'call'),
        'merge_clears_runtime_auto': point('body_merge', 0x4B70E611, 'mov', 0x558, register='r14d'),
    }
    assert not any(o.type == X86_OP_MEM and o.mem.disp == 0x558 for i in instructions['atom_feature_serializer'].values() for o in i.operands)
    assert unpack('<Q', pe.get_data(0x4CE93810-base+0x28, 8))[0] == 0x4BBA6B10
    thunk = next(engine.disasm(pe.get_data(0x4BBA6B10-base, 5), 0x4BBA6B10))
    assert thunk.mnemonic == 'jmp' and thunk.operands[0].imm == 0x4BBA4390
    return {
        'schema': 'kit.sw2026.cold-selected-body-construction.v1',
        'module': 'sldmodu.dll', 'module_sha256': PIN, 'image_base': hex(base), 'document_version': 19000,
        'native_ranges': ranges, 'independently_checked_sites': checks,
        'scope_word': {'wire_owner': 'moAtomFeature_c.f544', 'selected': 1, 'all_bodies': 0},
        'runtime_auto_select': {'native_offset': '0x558', 'serialized_by_reached_owner': False, 'writer_input': False},
        'one_body_route': {'requires': ['ordinary rigid part', 'selected scope', 'runtime auto zero', 'one selected wrapper', 'one actual regenerated solid', 'wrapper owned by model unit component', 'positive wrapper f18 equals actual regenerated body atom id', 'empty runtime wrapper entity cache'], 'does_not_require_saved_face_reference': True, 'native_execution_proven': False},
        'first_boss_lineage_rule': {'atom_id': 'actual fresh manager counter + 1', 'base_feature': 'actual sole boss output owner f08', 'lineage': ['same actual sole boss atom f140'], 'termination': 'the producing boss has no consumed atom array', 'values_from_saved_documents': False},
        'fresh_wrapper_tail': {'ff0': None, 'f100': 0, 'f104': 0, 'f108': -1, 'n110': 0, 'f110': []},
        'derived_selection_snapshot_tail': {'ff0': None, 'f100': 0, 'f104': 0, 'f108': 'actual base boss feature f08', 'n110': 'length of actual base atom walk', 'f110': 'actual base atom f140 values'},
        'cold_atom_reuse_dependency': 'NamedBodyColdReuse2026.md',
        'limits': ['no general multiple body chooser algorithm', 'no serializable continuously automatic-selection flag established', 'no scope-1 cold native acceptance', 'no full source or original held-out qualification', 'no public writer registration'],
        'heldout_payloads_read': 0, 'native_processes_started': 0, 'vendor_listing_included': False,
    }


parser = ArgumentParser()
parser.add_argument('--module', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
result = collect(args.module)
result['tool_sha256'] = sha256(Path(__file__).read_bytes()).hexdigest()
encoded = (json.dumps(result, indent=2, sort_keys=True)+'\n').encode()
if args.check:
    assert args.output.read_bytes() == encoded
else:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
print(json.dumps({'passed': True, 'sha256': sha256(encoded).hexdigest(), 'bytes': len(encoded), 'checked_sites': len(result['independently_checked_sites'])}))
