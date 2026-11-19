import argparse
from collections import defaultdict
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from struct import unpack_from
import sys


def require(value, reason):
    if not value:
        raise ValueError(reason)


def load_reader(root, expected):
    path = root / "re/tooling/sw2026/freecad_cylinder/NativeNamePe.py"
    require(sha256(path.read_bytes()).hexdigest() == expected, "shared PE reader source differs")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("cylinder_direction_pe", path)
    require(spec is not None and spec.loader is not None, "shared PE reader cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.NativeNamePe


def exports(image):
    address, size = unpack_from("<II", image.data, image.optional + 112)
    require(address and size, "selected native image has no export table")
    row = unpack_from("<IIHHIIIIIII", image.data, image.offset(address))
    base, total, count, functions, names, ordinals = row[5:]
    result = {}
    for index in range(count):
        name = image.ascii(unpack_from("<I", image.data, image.offset(names) + index * 4)[0])
        ordinal = unpack_from("<H", image.data, image.offset(ordinals) + index * 2)[0]
        require(ordinal < total, "native export ordinal exceeds its table")
        target = unpack_from("<I", image.data, image.offset(functions) + ordinal * 4)[0]
        if address <= target < address + size:
            continue
        result[name] = image.base + target
    return result


def unwind_groups(image):
    address, size = unpack_from("<II", image.data, image.optional + 112 + 3 * 8)
    require(address and size % 12 == 0, "native exception directory framing differs")
    rows = [unpack_from("<III", image.data, image.offset(address) + index) for index in range(0, size, 12)]
    cache = {}

    def ancestor(row):
        if row in cache:
            return cache[row]
        seen, current = set(), row
        while current not in seen:
            seen.add(current)
            begin, end, metadata = current
            offset = image.offset(metadata)
            flags = image.data[offset] >> 3
            if not flags & 4:
                for item in seen:
                    cache[item] = current
                return current
            count = image.data[offset + 2]
            current = unpack_from("<III", image.data, offset + 4 + ((count + 1) // 2) * 4)
        raise ValueError("native chained unwind cycle")

    groups = defaultdict(list)
    for row in rows:
        groups[ancestor(row)].append(row)
    return rows, groups, ancestor


def pin_function(image, entry, rows, groups, ancestor, leaf_bytes=None):
    relative = int(entry, 16) - image.base
    matches = [row for row in rows if row[0] <= relative < row[1]]
    if matches:
        require(len(matches) == 1, "native entry belongs to multiple unwind fragments")
        primary = ancestor(matches[0])
        require(primary[0] == relative, "native entry is not the primary function start")
        parts = sorted(groups[primary])
    else:
        require(type(leaf_bytes) is int and 0 < leaf_bytes <= 128, "leaf function needs an exact bounded length")
        parts = [(relative, relative + leaf_bytes, None)]
    chunks, fragments = [], []
    for begin, end, metadata in parts:
        raw = image.data[image.offset(begin, end - begin):image.offset(begin, end - begin) + end - begin]
        chunks.append(raw)
        fragments.append({"begin": hex(image.base + begin), "end_exclusive": hex(image.base + end),
                          "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
                          "unwind_flags": None if metadata is None else image.data[image.offset(metadata)] >> 3})
    return {"entry": entry, "fragment_count": len(fragments), "fragments": fragments,
            "total_bytes": sum(len(raw) for raw in chunks), "ordered_fragment_sha256": sha256(b"".join(chunks)).hexdigest()}


def pin_class(image, selected, names):
    name = selected["name"]
    symbol = selected["descriptor_symbol"]
    require(symbol in names, "selected runtime descriptor export is absent")
    address = names[symbol]
    offset = image.offset(address - image.base, 32)
    pointer, size, schema, creator, base_resolver = unpack_from("<QIIQQ", image.data, offset)
    actual_name = image.ascii(pointer - image.base)
    require(actual_name == name, "runtime descriptor name differs")
    vtable = int(selected["vtable"], 16)
    serializer = unpack_from("<Q", image.data, image.offset(vtable - image.base) + 5 * 8)[0]
    require(hex(serializer) == selected["serializer"], "selected vtable serializer differs")
    return {"name": name, "descriptor": hex(address), "object_bytes": size, "raw_schema": schema,
            "archive_schema": schema & 0x7FFFFFFF, "creator": hex(creator), "base_resolver": hex(base_resolver),
            "vtable": hex(vtable), "serializer": hex(serializer)}


def pin_call(image, selected):
    address = int(selected["site"], 16)
    offset = image.offset(address - image.base, 6)
    raw = image.data[offset:offset + 6]
    if selected["kind"] == "direct":
        require(raw[0] == 0xE8, "expected relative native call is absent")
        target = address + 5 + unpack_from("<i", raw, 1)[0]
        require(hex(target) == selected["target"], "native call target differs")
        return {"site": selected["site"], "kind": "direct", "target": hex(target)}
    require(selected["kind"] == "import" and raw[:2] == b"\xff\x15", "expected native import call is absent")
    target = address + 6 + unpack_from("<i", raw, 2)[0]
    require(hex(target) == selected["iat"], "native import slot differs")
    binding = image.imports()[target]
    require(binding["name"] == selected["symbol"], "native imported symbol differs")
    return {"site": selected["site"], "kind": "import", "iat": hex(target), "binding": binding}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--framework", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "output must be new")
    knowledge_raw = args.knowledge.read_bytes()
    knowledge = json.loads(knowledge_raw)
    require(knowledge["schema"] == "kit.sw2026.cylinder-direction-wire.v1", "knowledge schema differs")
    require(knowledge["document_version"] == 19000, "direction wire scope requires version 19000")
    reader = load_reader(args.root, knowledge["pe_reader_sha256"])
    images = {"sldmodu": reader(args.model.read_bytes()), "sldmfcu": reader(args.framework.read_bytes())}
    names, groups, identity = {}, {}, []
    for name, image in images.items():
        expected = knowledge["modules"][name]
        require(image.sha256 == expected["sha256"] and len(image.data) == expected["bytes"]
                and hex(image.base) == expected["base"] and image.machine == 0x8664, "pinned original image differs")
        names[name] = exports(image)
        groups[name] = unwind_groups(image)
        identity.append({"name": name, "sha256": image.sha256, "bytes": len(image.data), "base": hex(image.base)})
    functions = {}
    for selected in knowledge["functions"]:
        module = selected["module"]
        if "symbol" in selected:
            require(hex(names[module][selected["symbol"]]) == selected["entry"], "exported entry differs")
        functions[selected["key"]] = pin_function(images[module], selected["entry"], *groups[module], selected.get("leaf_bytes"))
    classes = [pin_class(images["sldmodu"], selected, names["sldmodu"]) for selected in knowledge["classes"]]
    calls = [pin_call(images[selected["module"]], selected) for selected in knowledge["calls"]]
    slots = []
    for selected in knowledge["virtual_slots"]:
        image = images["sldmodu"]
        target = unpack_from("<Q", image.data, image.offset(int(selected["vtable"], 16) - image.base) + selected["slot_bytes"])[0]
        require(hex(target) == selected["target"], "native selected-geometry virtual target differs")
        slots.append(dict(selected))
    result = {"schema": "kit.sw2026.cylinder-direction-wire-pin.v1", "source_pin_passed": True,
              "knowledge_sha256": sha256(knowledge_raw).hexdigest(),
              "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "modules": identity,
              "functions": functions, "classes": classes, "calls": calls, "virtual_slots": slots,
              "semantic_confidence": "partial: static source only; no non-null source corpus or native output acceptance",
              "generated_native_files": 0, "native_processes_started": 0, "heldout_inputs_read": 0,
              "hopper_documents_opened": 0}
    encoded = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(json.dumps({"source_pin_passed": True, "sha256": sha256(encoded).hexdigest(),
                      "function_count": len(functions), "class_count": len(classes), "call_count": len(calls),
                      "generated_native_files": 0, "native_processes_started": 0, "heldout_inputs_read": 0}))


if __name__ == "__main__":
    main()
