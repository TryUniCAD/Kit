from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct

from CollectDrawingViewSupportEvidence import Image


def module(image, expected):
    digest = sha256(image.data).hexdigest()
    if digest != expected or image.machine != 0x8664:
        raise ValueError("original module identity differs")
    return {"name": image.path.name, "sha256": digest, "machine": hex(image.machine), "image_base": hex(image.base)}


def vocabulary(image, identifiers):
    resource_rva, _ = image.directories[2]
    resource_base = image.offset(resource_rva)

    def entries(relative):
        offset = resource_base + relative
        count = image.unpack("H", offset + 12) + image.unpack("H", offset + 14)
        return dict(struct.unpack_from("<II", image.data, offset + 16 + index * 8) for index in range(count))

    strings = entries(entries(0)[6] & 0x7FFFFFFF)
    result = []
    for identifier in identifiers:
        block_id = identifier // 16 + 1
        leaf = entries(strings[block_id] & 0x7FFFFFFF)[1033] & 0x7FFFFFFF
        data_rva, length, _, _ = struct.unpack_from("<IIII", image.data, resource_base + leaf)
        cursor = image.offset(data_rva)
        for index in range(16):
            size = image.unpack("H", cursor)
            cursor += 2
            text = image.data[cursor:cursor + 2 * size].decode("utf-16-le")
            cursor += 2 * size
            if index == identifier % 16:
                result.append({"resource_id": hex(identifier), "language_id": 1033, "text": text,
                               "block_id": block_id, "data_rva": hex(data_rva), "block_bytes": length})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("choose an unused source evidence path")
    model = Image(args.binaries / "sldmodu.dll")
    resources = Image(args.binaries / "sldresu.dll")
    routines = {
        "create_default_lights": 0x4C019C60,
        "make_notes_area_if_needed": 0x4C013AF0,
        "add_notes_folder": 0x4BEC0970,
        "make_notes_partner": 0x4BEC9E10,
        "add_folder_pair": 0x4BEBFC20,
        "register_folder_to_model": 0x4BECC360,
        "create_light_by_type": 0x4BC0C800,
    }
    leaves = {
        "ambient_base_name": (0x4BC0CBB0, 0x4BC0CBBF),
        "directional_base_name": (0x4BC0CBC0, 0x4BC0CBCF),
        "notes_base_name": (0x4BEC5F40, 0x4BEC5F85),
        "model_environment_pointer": (0x4B2863B0, 0x4B2863B8),
    }
    result = {
        "schema": "kit.sw2026.system-presentation-source.v1",
        "modules": [module(model, "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"),
                    module(resources, "531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111")],
        "routines": {name: model.function(address) for name, address in routines.items()},
        "bounded_leaf_ranges": {name: {"start_va": hex(start), "end_va_exclusive": hex(end),
                                       "code_sha256": sha256(model.bytes(start, end)).hexdigest(),
                                       "scope": "bounded instructions only; not an inferred unwind extent"}
                                for name, (start, end) in leaves.items()},
        "english_resource_vocabulary": vocabulary(resources, (0x73A9, 0x3142, 0x3140)),
        "imports": {hex(address): model.imports[address] for address in (0x4CD3C498, 0x4CD34E70, 0x4CD34E48)},
        "folder_end_name_formats": [{"va": hex(address), "text": model.bytes(address, address + 64).decode("utf-16-le", errors="strict").split("\0")[0]}
                                    for address in (0x4D0941B0, 0x4D0941D0)],
        "rules": {
            "default_lights": "Session Environment virtual 0x188 returns the named Default settings collection; the model constructs and attaches one light per actual entry, not a fixed four-light array",
            "note_owner": "MakeNotesAreaAnnotationViewIfNeeded finds the actual cabinet then searches and inserts NotesAreaFtrFolder nodes in that cabinet",
            "note_pair": "makePartner stores reciprocal f388 pointers and clears partner f37c; AddFolder marks the head and registers both nodes",
            "cabinet_placement": "The observed ordinary profile places the cabinet after the document folder; no universal insertion-order claim",
            "implicit_labels": "The English resource vocabulary and unique-name format support the measured empty-owner profile, with no persisted default scalar state inferred",
        },
        "source_only": True, "vendor_runtime_executed": False, "heldout_inputs_read": 0,
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.output), "sha256": sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
