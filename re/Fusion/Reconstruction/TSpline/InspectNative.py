import bisect
import hashlib
import json
import runpy
import struct
from pathlib import Path


BASE = Path(__file__).resolve().parent
TOOLS = runpy.run_path(str(BASE.parent / "ReadBinaryMembers.py"))
APP = Path("/Users/odin/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents")
RELATIVE = "Frameworks/ASM/libtsplines.14.dylib"


def layout(binary):
    header = struct.unpack_from("<IIIIIIII", binary.data, binary.offset)
    position = binary.offset + 32
    sections, starts = [], []
    for _ in range(header[4]):
        kind, size = struct.unpack_from("<II", binary.data, position)
        if kind == 0x19:
            section_count = struct.unpack_from("<I", binary.data, position + 64)[0]
            for index in range(section_count):
                name, segment, address, length, offset = struct.unpack_from("<16s16sQQI", binary.data, position + 72 + 80 * index)
                sections.append({"name": name.rstrip(b"\0").decode(), "segment": segment.rstrip(b"\0").decode(), "address": address, "length": length, "offset": binary.offset + offset})
        if kind == 0x26:
            offset, length = struct.unpack_from("<II", binary.data, position + 8)
            value, shift, current = 0, 0, 0
            for byte in binary.data[binary.offset + offset:binary.offset + offset + length]:
                value |= (byte & 127) << shift
                if byte < 128:
                    if value == 0:
                        break
                    current += value
                    starts.append(current)
                    value, shift = 0, 0
                else:
                    shift += 7
        position += size
    return sections, starts


def literals(binary, sections):
    values = ["100edges", "100verts", "100edges 100verts", "50000vert 50000grip", "N6tskern8ExCreaseE", "N6tskern11ExSmartGripE", "N6tskern8ExFreezeE", "N6tskern10ExSymmetryE", "N6tskern11ExUserKnotsE", "{}CreasedBorderEdges", "{}CreasedCornerVerts", "m odd-grip-map", "#TS0200"]
    found = {}
    for value in values:
        needle = value.encode() + b"\0"
        for section in sections:
            data = binary.data[section["offset"]:section["offset"] + section["length"]]
            offset = data.find(needle)
            while offset >= 0:
                address = section["address"] + offset
                found[address] = value
                offset = data.find(needle, offset + 1)
    return found


def references(binary, section, targets, starts):
    data = binary.data[section["offset"]:section["offset"] + section["length"]]
    words = [row[0] for row in struct.iter_unpack("<I", data)]
    result = []
    for index, word in enumerate(words):
        if word & 0x9F000000 != 0x90000000:
            continue
        address = section["address"] + index * 4
        register = word & 31
        immediate = ((word >> 29) & 3) | (((word >> 5) & 0x7FFFF) << 2)
        if immediate & (1 << 20):
            immediate -= 1 << 21
        page = (address & ~0xFFF) + (immediate << 12)
        for follow in range(index + 1, min(index + 9, len(words))):
            operation = words[follow]
            if operation & 0xFFC00000 == 0x91000000 and (operation >> 5) & 31 == register:
                target = page + ((operation >> 10) & 0xFFF)
                if target in targets:
                    at = section["address"] + follow * 4
                    function = starts[bisect.bisect_right(starts, at) - 1]
                    end = starts[bisect.bisect_right(starts, at)]
                    result.append({"string": targets[target], "string_address": hex(target), "adrp": hex(address), "add": hex(at), "function_start": hex(function), "function_end": hex(end)})
    return result


def type_tables(binary, sections, targets):
    pointers = []
    for section in sections:
        if section["segment"] not in ("__DATA", "__DATA_CONST"):
            continue
        for offset in range(0, section["length"] - 7, 8):
            word = struct.unpack_from("<Q", binary.data, section["offset"] + offset)[0]
            pointers.append((section["address"] + offset, word & 0xFFFFFFFFFFFF))
    result = []
    for name_address, name in targets.items():
        if not name.startswith("N6tskern"):
            continue
        for pointer, target in pointers:
            if target != name_address:
                continue
            type_info = pointer - 8
            tables = []
            for entry, destination in pointers:
                if destination == type_info:
                    table = entry + 8
                    raw = binary.read(table, 8 * 20)
                    tables.append({"address": hex(table), "slots": [hex(value & 0xFFFFFFFFFFFF) for value in struct.unpack("<" + "Q" * 20, raw)]})
            result.append({"name": name, "type_info": hex(type_info), "vtables": tables})
    return result


def main():
    binary = TOOLS["Binary"](APP / RELATIVE)
    sections, starts = layout(binary)
    targets = literals(binary, sections)
    section = next(row for row in sections if row["name"] == "__text")
    report = {"scope": "Static ARM64 string references and RTTI/vtable provenance; no library execution", "application_version": "2706.1.17", "image": RELATIVE, "sha256": binary.sha256, "address_basis": "Unslid ARM64 Mach-O virtual addresses", "function_starts": len(starts), "literals": {hex(key): value for key, value in targets.items()}, "references": references(binary, section, targets, starts), "extension_vtables": type_tables(binary, sections, targets)}
    (BASE / "NativeEvidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
