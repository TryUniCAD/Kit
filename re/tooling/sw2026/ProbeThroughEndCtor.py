from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

PIN = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
VTABLE = 0x4CF3D3F8


def collect(module):
    payload = module.read_bytes()
    if sha256(payload).hexdigest() != PIN:
        raise ValueError("the exact pinned original 2026 model image is required")
    pe = pefile.PE(data=payload, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]])
    engine = Cs(CS_ARCH_X86, CS_MODE_64)
    engine.detail = True
    getter = unpack("<Q", pe.get_data(VTABLE - base, 8))[0]
    instruction = next(engine.disasm(pe.get_data(getter - base, 7), getter))
    assert instruction.mnemonic == "lea" and instruction.reg_name(instruction.operands[1].mem.base) == "rip"
    runtime = instruction.address + instruction.size + instruction.operands[1].mem.disp
    name, size, schema, factory = unpack("<QIIQ", pe.get_data(runtime - base, 24))
    assert pe.get_string_at_rva(name - base) == b"moEndSpec_c" and size == 0x160 and schema == 0x80000001
    factory_calls = [item.operands[0].imm for item in engine.disasm(pe.get_data(factory - base, 0x27), factory) if item.mnemonic == "call" and item.operands[0].type == X86_OP_IMM]
    assert len(factory_calls) == 1
    constructor = factory_calls[0]
    end = next(base + item.struct.EndAddress for item in pe.DIRECTORY_ENTRY_EXCEPTION if base + item.struct.BeginAddress == constructor)
    body = pe.get_data(constructor - base, end - constructor)
    alias = None
    zero = set()
    stores = []
    installed = None
    for item in engine.disasm(body, constructor):
        operands = item.operands
        if item.mnemonic == "mov" and len(operands) == 2 and all(value.type == X86_OP_REG for value in operands):
            if item.reg_name(operands[1].reg) == "rcx":
                alias = item.reg_name(operands[0].reg)
        if item.mnemonic == "xor" and len(operands) == 2 and all(value.type == X86_OP_REG for value in operands) and operands[0].reg == operands[1].reg:
            register = item.reg_name(operands[0].reg)
            zero.update(("eax", "rax") if register in ("eax", "rax") else (register,))
        if item.mnemonic == "lea" and item.reg_name(operands[0].reg) == "rax" and operands[1].type == X86_OP_MEM and item.reg_name(operands[1].mem.base) == "rip":
            installed = item.address + item.size + operands[1].mem.disp
        if item.mnemonic != "mov" or len(operands) != 2 or operands[0].type != X86_OP_MEM or item.reg_name(operands[0].mem.base) != alias:
            continue
        source = operands[1]
        value = source.imm if source.type == X86_OP_IMM else 0 if source.type == X86_OP_REG and item.reg_name(source.reg) in zero else None
        if value == 0:
            stores.append({"instruction": hex(item.address), "offset": operands[0].mem.disp, "bytes": operands[0].size, "value": 0})
    assert installed == VTABLE
    fields = {}
    for offset in (0x148, 0x14C, 0x150, 0x154, 0x158):
        match = [row for row in stores if row["offset"] <= offset and offset + 4 <= row["offset"] + row["bytes"]]
        assert len(match) == 1
        fields[f"f{offset:x}"] = {**match[0], "wire_type": "i32", "constructor_value": 0, "saved_semantic_meaning": "capped mid-plane surface extrusion flag" if offset == 0x158 else "not established by this probe"}
    return {"schema": "kit.sw2026.through-all-end-default-constructor.v1", "module": "sldmodu.dll", "module_sha256": PIN, "document_version": 19000, "vtable": hex(VTABLE), "runtime_class": hex(runtime), "get_runtime_class": hex(getter), "create_object": hex(factory), "object_size": size, "runtime_schema": schema, "constructor": {"entry": hex(constructor), "end": hex(end), "bytes": len(body), "sha256": sha256(body).hexdigest()}, "fields": fields, "rule": "fresh ordinary end records use the native constructor's explicit scalar zero stores; saved runtime words are not writer inputs", "native_processes_started": 0, "heldout_payloads_read": 0, "vendor_listing_included": False, "native_writer_acceptance": False}


parser = ArgumentParser()
parser.add_argument("--module", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
result = collect(args.module)
result["tool_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
if args.check:
    assert args.output.read_bytes() == encoded
else:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
print(json.dumps({"passed": True, "bytes": len(encoded), "sha256": sha256(encoded).hexdigest()}))
