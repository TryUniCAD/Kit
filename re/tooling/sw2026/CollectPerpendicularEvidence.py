from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess

from CollectDrawingViewSupportEvidence import Image, module, require


MODULES = {
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    "sldasmu.dll": "05ab90ee7380335088505c47202137c63dbce18d7d516e7fd6703aee31d70390",
}
ROUTINES = {
    "sldmodu.dll": {
        "runtime_class_getter": 0x4B6601C0,
        "runtime_class_allocator": 0x4B653CC0,
        "concrete_constructor": 0x4BC2E210,
        "ordinary_two_geometry_factory": 0x4BC42030,
        "ordinary_two_geometry_initializer": 0x4BC5D920,
        "shared_serializer_entry_fragment": 0x4B668A60,
        "shared_serializer_store_return_fragment": 0x4B668D59,
        "perpendicular_help_query": 0x4BC60D40,
        "common_help_query": 0x4BC60CC0,
    },
    "sldasmu.dll": {
        "api_command_factory": 0x3F989A10,
        "ordinary_command_constructor": 0x3F7F5550,
        "ordinary_command_runner": 0x3F8267F0,
        "perpendicular_model_creation": 0x3F815FB0,
    },
}


def word(image, address):
    return struct.unpack("<Q", image.bytes(address, address + 8))[0]


def table(image, address, locator, type_name, offsets):
    require(word(image, address - 8) == locator, "the concrete RTTI locator changed")
    signature, displacement, _, type_rva, _, self_rva = struct.unpack("<6I", image.bytes(locator, locator + 24))
    require(signature == 1 and displacement == 0 and image.base + self_rva == locator,
            "the concrete RTTI locator is not a primary object")
    require(image.string(type_rva + 16) == type_name, "the concrete RTTI class changed")
    return {"va": hex(address), "rtti_locator_va": hex(locator), "rtti_class": type_name,
            "slots": {hex(offset): hex(word(image, address + offset)) for offset in offsets}}


def collect(binaries, listings=None):
    images = {name: Image(binaries / name) for name in MODULES}
    model, assembly = (images[name] for name in ("sldmodu.dll", "sldasmu.dll"))
    descriptor = 0x4DAC9BE0
    name_ptr, packed, allocate, base_class = struct.unpack("<4Q", model.bytes(descriptor, descriptor + 32))
    require(model.string(name_ptr - model.base) == "moMatePerpendicular" and packed == 0x80000001000004B8
            and allocate == 0x4B653CC0 and base_class == 0x4B653B70, "the perpendicular runtime descriptor changed")
    model_table = table(model, 0x4CFA2278, 0x4D338BF0, ".?AVmoMatePerpendicular@@",
                        (0, 0x28, 0x21F0, 0x2258, 0x22C8, 0x23B0, 0x23D0))
    ui_table = table(assembly, 0x3FC7F4E8, 0x3FD45190, ".?AVuiAssemblyMatePerpendicularCmd_c@@", (0xB8, 0x988))
    require(model_table["slots"]["0x28"] == "0x4b668a60" and model_table["slots"]["0x23d0"] == "0x4bc5d920"
            and ui_table["slots"]["0x988"] == "0x3f815fb0",
            "the ordinary factory dispatch changed")
    jump = struct.unpack("<25I", assembly.bytes(0x3F98AAC8, 0x3F98AB2C))
    require(assembly.base + jump[2] == 0x3F989B74, "the native perpendicular API dispatch changed")
    changes = []
    for offset in range(0, 0x2420, 8):
        first, second = (word(model, address + offset) for address in (0x4CFA2278, 0x4CF9FE10))
        if first != second:
            changes.append({"slot": hex(offset), "perpendicular": hex(first), "parallel": hex(second)})
    imports = {hex(address): assembly.imports[address] for address in (0x3FBE8EC0, 0x3FBEA690)}
    result = {
        "schema": "kit.sw2026.perpendicular-mate-native-source.v1", "document_version": 19000,
        "native_build": "34.5.2.0604", "modules": {name: module(image, MODULES[name]) for name, image in images.items()},
        "runtime_class": {"va": hex(descriptor), "name": "moMatePerpendicular", "object_bytes": packed & 0xFFFFFFFF,
                          "schema": hex(packed >> 32), "allocator": hex(allocate), "base_class_getter": hex(base_class)},
        "model_vtable": model_table, "command_vtable": ui_table, "imports": imports,
        "perpendicular_vs_parallel_primary_slot_differences": changes,
        "api_enum_switch": {"table_va": "0x3f98aac8", "perpendicular_api_value": 2, "case_va": hex(assembly.base + jump[2])},
        "alignment_binding": {"ignored_api_selection": True, "zero_argument_va": "0x3f989b90", "command_constructor_call_va": "0x3f989b99",
                              "command_alignment_offset": "0xe8", "model_alignment_offset": "0x3b4",
                              "no_assumed_post_solve_or_com_alignment_value": True},
        "factory_binding": {"descriptor_getter_call_va": "0x3f815fd9", "model_factory_call_va": "0x3f816004",
                            "model_initializer_slot": "0x23d0", "model_initializer_call_va": "0x4bc4209d"},
        "routines": {name: {role: image.function(address) for role, address in ROUTINES[name].items()} for name, image in images.items()},
        "limitations": ["Unwind entries describe fragments, not an asserted whole multi-fragment serializer body",
                        "The shared archive grammar does not qualify all eleven changed perpendicular virtual slots",
                        "Plane-only help-data and final solver state require independent authored controls",
                        "No new writer, vendor execution or native acceptance is established"],
        "heldout_inputs_read": 0, "native_processes_started": 0, "writer_output_count": 0,
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    if listings is not None:
        listings.mkdir(parents=True, exist_ok=False)
        for name, image in images.items():
            for role, address in ROUTINES[name].items():
                extent = image.function(address)
                lower = int(extent.get("start_va", hex(address)), 16)
                upper = int(extent.get("end_va_exclusive", hex(address + 16)), 16)
                recorded = subprocess.run(["/usr/bin/objdump", "-d", "--no-show-raw-insn", f"--start-address={lower}",
                                           f"--stop-address={upper}", str(image.path)], capture_output=True, check=True).stdout
                (listings / f"{name}-{role}.txt").write_bytes(recorded)
    return result


def main():
    parser = argparse.ArgumentParser(description="Bind ordinary perpendicular ownership to the exact original 2026 images without CAD")
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-listings", type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "use a fresh numeric source receipt")
    if args.private_listings is not None:
        require(not args.private_listings.resolve().is_relative_to(Path(__file__).resolve().parents[3]),
                "proprietary disassembly must stay outside the checkout")
    value = collect(args.binaries.resolve(strict=True), args.private_listings)
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    args.output.write_bytes(data)
    print(json.dumps({"sha256": sha256(data).hexdigest(), "native_processes_started": 0, "writer_output_count": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
