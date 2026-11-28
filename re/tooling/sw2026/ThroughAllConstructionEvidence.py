from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

from ManagedConstructionIndex import ManagedIndex

PINS = {
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    "sldcoreu.dll": "3af88769b06bf7a1510fe52f279fbda20e5dc5548dc3925a1357e0f71cc3b3e3",
    "sldappu.dll": "50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf",
    "slduiu.dll": "025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7",
}
FUNCTIONS = {
    "sldmodu.dll": {
        "getSingleEnd": 0x4B283BA0,
        "setSingleEnd": 0x4B2913B0,
        "getType": 0x4B30D800,
        "setType": 0x4B3100B0,
        "getFlip": 0x4B2A75E0,
        "setFlip": 0x4B2A7860,
        "getDirection": 0x4B2C47A0,
        "setDirection": 0x4B2C69A0,
        "getDistance": 0x4BADF660,
        "deleteNotUsedDims": 0x4BADA5B0,
        "recreateNecessaryDisplayDims": 0x4BAF4100,
        "genGcEndSpec": 0x4BADE750,
        "serializeEndSpec": 0x4BB10250,
        "serializeExtrusion": 0x4BB11640,
    },
    "sldappu.dll": {
        "FeatureExtrusion3": 0x4564BF70,
        "FeatureCut4": 0x4564A930,
        "loadFromMacro": 0x459EE330,
    },
    "slduiu.dll": {
        "iApiFeatureExtrusion4": 0x492546E0,
        "iApiFeatureCut7": 0x49252EC0,
        "endSpecDialogDataMap": 0x493E42A0,
    },
}
TOKENS = (
    0x06005036,
    0x06005037,
    0x06005038,
    0x06005039,
    0x0600503A,
    0x0600505A,
    0x06005069,
    0x0600506A,
    0x06005071,
    0x06005072,
    0x0600508B,
    0x0600508C,
)
RULES = {
    "native_type_owner": {
        "first": "f0c",
        "second": "f10",
        "width": "i32",
        "index_order": [0, 1],
        "setter_remaps": False,
    },
    "direction_owners": {
        "single_end": "f08",
        "flip": "f88",
        "direction": "f8c",
        "distance_displays": ["f18", "f20"],
    },
    "cleanup": {
        "entry": "0x4bada5b0",
        "first_distance_predicate": "1 <= unsigned(first_type) <= 4 and environment(0x33) == 0",
        "second_distance_predicate": "(single_end != 0 or 1 <= unsigned(second_type) <= 4) and environment(0x33) == 0",
        "action": "remove dimension configuration data, destroy actual display object, null the owning pointer",
        "environment_owner": "SldSession_c::Environment",
        "environment_virtual_offset": "0x78",
        "environment_selector": "0x33",
        "environment_selector_semantics": "not yet bound",
        "draft_displays": ["fc8", "fd0"],
        "draft_enabled": ["fb8", "fbc"],
    },
    "recreate_distance_displays": {
        "entry": "0x4baf4100",
        "ends_visited": [0, 1],
        "prune_predicate": "((single_end != 0 and end == 1) or 1 <= unsigned(type[end]) <= 4) and environment(0x33) == 0",
        "prune_action": "destroy actual distance display and null its pointer; do not allocate a replacement",
        "opposite_branch": "retain or allocate a moDisplayDistanceDim_c using ParallelPlaneDistanceDim_c; role is end+1",
        "draft_roles": [3, 4],
        "transient_from_offset_role": 19,
        "status": "partial until the new native sources exercise the branch",
    },
    "managed_current_end_spec": {
        "token": "0x0600503a",
        "native_end_spec_offset": "0x818",
        "class_by_native_type": {
            "0": "BlindEndSpec_c",
            "1": None,
            "2": None,
            "3": "ToPointEndSpec_c",
            "4": "ToSurfaceEndSpec_c",
            "5": "OffsetFromSurfaceEndSpec_c",
            "6": "MidPlaneEndSpec_c",
            "7": "UpToBodyEndSpec_c",
        },
        "default": None,
        "public_enum_9_mapping_inferred": False,
    },
    "blind_distance_publication": {
        "token": "0x06005072",
        "base_apply_first": True,
        "native_calls_in_order": ["setDistance", "setType"],
        "native_type_argument": 0,
        "through_all_constructor": False,
    },
    "through_all_both_source_encoding": {
        "api_single_direction": False,
        "forward_type": 1,
        "reverse_type": 1,
        "public_enum_9_exercised": False,
        "native_source_verification": "pending",
    },
    "boss_finite_extent": {
        "status": "not found",
        "writer_admission": False,
        "stock_span_formula": "unverified hypothesis only",
    },
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def function_fact(image, address):
    base = image.OPTIONAL_HEADER.ImageBase
    rva = address - base
    entries = [
        row.struct
        for row in image.DIRECTORY_ENTRY_EXCEPTION
        if row.struct.BeginAddress <= rva < row.struct.EndAddress
    ]
    if entries:
        (row,) = entries
        if row.BeginAddress != rva:
            raise ValueError("The pinned native symbol is not at its unwind entry")
        end = row.EndAddress
        provenance = "PE-x64-unwind-primary-range"
        limits = "primary unwind range; separate chained funclets are not claimed"
    else:
        decoder = Cs(CS_ARCH_X86, CS_MODE_64)
        instructions = list(decoder.disasm(image.get_data(rva, 96), address))
        candidates = [item for item in instructions if item.mnemonic.startswith("ret")]
        if not candidates:
            raise ValueError("The pinned leaf has no bounded return")
        first = candidates[0]
        prefix = [item for item in instructions if item.address <= first.address]
        if any(
            item.mnemonic.startswith("j") or item.mnemonic == "call" for item in prefix
        ):
            raise ValueError(
                "A leaf return is not sufficient for nontrivial control flow"
            )
        end = first.address + first.size - base
        provenance = "straight-line-leaf-through-return"
        limits = "only the verified straight-line leaf"
    body = image.get_data(rva, end - rva)
    return {
        "entry_address": hex(address),
        "primary_range": {
            "start_inclusive": hex(address),
            "end_exclusive": hex(base + end),
        },
        "bytes": len(body),
        "sha256": digest(body),
        "extent_authority": provenance,
        "limitations": limits,
    }


def collect(root):
    pefile.MAX_IMPORT_SYMBOLS = 100000
    images, modules = {}, {}
    for name, expected in PINS.items():
        path = root / name
        raw = path.read_bytes()
        if digest(raw) != expected:
            raise ValueError("Pinned module identity mismatch: " + name)
        image = pefile.PE(str(path), max_symbol_exports=100000)
        if (
            len(image.DIRECTORY_ENTRY_EXPORT.symbols)
            != image.DIRECTORY_ENTRY_EXPORT.struct.NumberOfFunctions
        ):
            raise ValueError("Incomplete native export inventory")
        images[name] = image
        modules[name] = {
            "sha256": expected,
            "bytes": len(raw),
            "image_base": hex(image.OPTIONAL_HEADER.ImageBase),
            "declared_exports": image.DIRECTORY_ENTRY_EXPORT.struct.NumberOfFunctions,
            "parsed_exports": len(image.DIRECTORY_ENTRY_EXPORT.symbols),
        }
    managed = ManagedIndex(root / "sldcoreu.dll", PINS["sldcoreu.dll"], None, None)
    managed.native, managed.native_identity = images["sldmodu.dll"], {
        "name": "sldmodu.dll",
        **modules["sldmodu.dll"],
    }
    managed.native_exports = {
        row.name.decode("ascii"): row
        for row in managed.native.DIRECTORY_ENTRY_EXPORT.symbols
        if row.name
    }
    facts = {
        name: {
            key: function_fact(images[name], address)
            for key, address in entries.items()
        }
        for name, entries in FUNCTIONS.items()
    }
    return {
        "schema": "kit.sw2026.through-all-construction-evidence.v1",
        "native_build": "34.5.2.0604",
        "document_version": 19000,
        "task": "B04-SW2026-EXTRUDE-THROUGHALL",
        "owner": "assembly_occurrence",
        "delivery_pr": 121,
        "tool_sha256": digest(Path(__file__).read_bytes()),
        "module_identities": modules,
        "native_functions": facts,
        "managed_construction": managed.receipt(TOKENS, False),
        "rules": RULES,
        "parser_versions": {
            name: importlib.metadata.version(name)
            for name in ("pefile", "dnfile", "dncil", "capstone")
        },
        "native_processes_started": 0,
        "new_heldout_inputs_read": 0,
        "writer_output_count": 0,
        "vendor_listings_included": False,
        "native_acceptance": False,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce hash-bound through-all construction facts without retaining vendor code or running CAD"
    )
    parser.add_argument("modules", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = collect(args.modules.resolve(strict=True))
    encoded = (json.dumps(value, indent=2) + "\n").encode()
    if args.check:
        if args.output.read_bytes() != encoded:
            raise ValueError("The through-all construction evidence differs")
    else:
        args.output.write_bytes(encoded)
    print(
        json.dumps(
            {
                "sha256": digest(encoded),
                "checked": args.check,
                "vendor_code_emitted": False,
                "writer_output_count": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
