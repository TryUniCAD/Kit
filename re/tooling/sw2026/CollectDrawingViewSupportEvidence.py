from __future__ import annotations

import argparse
from bisect import bisect_right
from hashlib import sha256
import json
from pathlib import Path
import struct


class Image:
    def __init__(self, path):
        self.path = path
        self.data = path.read_bytes()
        header = self.unpack("I", 0x3C)
        self.machine = self.unpack("H", header + 4)
        optional = header + 24
        self.base = self.unpack("Q", optional + 24)
        sections = optional + self.unpack("H", header + 20)
        self.sections = [struct.unpack_from("<8sIIIIIIHHI", self.data, sections + index * 40)
                         for index in range(self.unpack("H", header + 6))]
        self.directories = [struct.unpack_from("<II", self.data, optional + 112 + index * 8) for index in range(16)]
        self.exports = {}
        names = struct.unpack_from("<IIHHIIIIIII", self.data, self.offset(self.directories[0][0]))
        count, addresses, strings, ordinals = names[7:]
        for index in range(count):
            name = self.string(self.unpack("I", self.offset(strings) + index * 4))
            ordinal = self.unpack("H", self.offset(ordinals) + index * 2)
            address = self.base + self.unpack("I", self.offset(addresses) + ordinal * 4)
            self.exports.setdefault(address, []).append(name)
        self.imports = {}
        cursor = self.offset(self.directories[1][0])
        while any(row := struct.unpack_from("<IIIII", self.data, cursor)):
            original, _, _, library, table = row
            index = 0
            while entry := self.unpack("Q", self.offset(original or table) + index * 8):
                self.imports[self.base + table + index * 8] = {
                    "module": self.string(library),
                    "symbol": f"#{entry & 65535}" if entry >> 63 else self.string(entry + 2),
                }
                index += 1
            cursor += 20
        start, length = self.directories[3]
        self.functions = [struct.unpack_from("<III", self.data, self.offset(start) + index)
                          for index in range(0, length, 12)]
        self.starts = [row[0] for row in self.functions]

    def unpack(self, fmt, offset):
        return struct.unpack_from("<" + fmt, self.data, offset)[0]

    def offset(self, rva):
        for section in self.sections:
            if section[2] <= rva < section[2] + max(section[1], section[3]):
                return section[4] + rva - section[2]
        raise ValueError(f"unmapped RVA {rva:x}")

    def string(self, rva):
        offset = self.offset(rva)
        return self.data[offset:self.data.index(0, offset)].decode()

    def bytes(self, start, end):
        return self.data[self.offset(start - self.base):self.offset(end - self.base)]

    def function(self, address):
        start, end, unwind = self.functions[bisect_right(self.starts, address - self.base) - 1]
        if not start <= address - self.base < end:
            return {"requested_va": hex(address), "unwind_entry_found": False,
                    "exact_exports": self.exports.get(address, [])[:10],
                    "exact_export_alias_count": len(self.exports.get(address, [])),
                    "entry_sample_bytes": 16,
                    "entry_sample_sha256": sha256(self.bytes(address, address + 16)).hexdigest()}
        return {"start_va": hex(self.base + start), "end_va_exclusive": hex(self.base + end),
                "start_rva": hex(start), "end_rva_exclusive": hex(end), "unwind_rva": hex(unwind),
                "exact_exports": self.exports.get(self.base + start, [])[:10],
                "exact_export_alias_count": len(self.exports.get(self.base + start, [])),
                "code_sha256": sha256(self.bytes(self.base + start, self.base + end)).hexdigest()}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def module(image, expected):
    digest = sha256(image.data).hexdigest()
    require(digest == expected and image.machine == 0x8664, "pinned original module differs")
    return {"name": image.path.name, "sha256": digest, "bytes": len(image.data),
            "image_base": hex(image.base), "machine": hex(image.machine)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    require(not arguments.output.exists(), "choose an unused source evidence receipt")
    model = Image(arguments.binaries / "sldmodu.dll")
    geometry = Image(arguments.binaries / "sldmgu.dll")
    model_routines = {
        "create_profile_feature": 0x4C9952B0,
        "create_absolute_default_plane": 0x4C2D3FE0,
        "create_drawing_default_plane": 0x4C2D40D0,
        "finish_creating_view": 0x4C998070,
        "set_drawing_scale": 0x4C2BC360,
        "get_or_create_sheet_sketch": 0x4C9A3CB0,
        "get_or_create_center_mark_sketch": 0x4C9A3B10,
        "center_mark_creation_body": 0x4C9A3B44,
        "center_mark_plane_reframe": 0x4C9B4740,
        "set_sketch_xforms": 0x4C0E5280,
        "get_four_corners": 0x4C2E57C0,
        "update_name_location": 0x4C2F72C0,
        "set_name_location": 0x4C2CF0C0,
        "is_okay_to_2d_dimension": 0x4C9AEAF0,
        "set_is_okay_to_2d_dimension": 0x4C9B64E0,
        "set_is_view_face_valid": 0x4C9B6530,
        "set_manual_regeneration": 0x4C9B66E0,
        "absolute_view_dimension_override": 0x4B745630,
    }
    imports = (0x4CD3A648, 0x4CD3A668, 0x4CD3A680, 0x4CD3A690, 0x4CD3A908,
               0x4CD3A988, 0x4CD3A9D0, 0x4CD3AB40, 0x4CD3BE10)
    result = {
        "schema": "kit.sw2026.drawing-support-native-source-locations.v1",
        "modules": [module(model, "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"),
                    module(geometry, "99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c")],
        "model_routines": {name: model.function(address) for name, address in model_routines.items()},
        "geometry_is_orthogonal": geometry.function(0x31F1B170),
        "model_imports": {hex(address): model.imports[address] for address in imports},
        "orthogonal_tolerance": {"va": "0x31f44800", "type": "f64-le", "value": struct.unpack("<d", geometry.bytes(0x31F44800, 0x31F44808))[0]},
        "absolute_view_vtable": {"va": "0x4ce83fb8", "dimension_override_slot": "0x2060",
                                 "target_va": hex(model.unpack("Q", model.offset(0x4CE83FB8 + 0x2060 - model.base)))},
        "heldout_inputs_read": 0, "writer_outputs": 0, "vendor_runtime_executed": False,
        "source_only": True, "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    arguments.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(arguments.output), "sha256": sha256(arguments.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
