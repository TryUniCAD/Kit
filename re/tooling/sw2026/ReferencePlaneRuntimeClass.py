import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


MODEL_SHA256 = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
ARCHIVE_SHA256 = "d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c"
CLASSES = ("moConstraintDefaultPlaneRefplaneData_c", "moConstraintRefplaneData_c", "moRefPlaneDistanceGeom_c")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def publication(image, name, row):
    base = image.OPTIONAL_HEADER.ImageBase
    vtable = int(row["vtable"], 16)
    get_class, = struct.unpack("<Q", image.get_data(vtable - base, 8))
    code = image.get_data(get_class - base, 8)
    if code[:3] != b"\x48\x8d\x05" or code[7:] != b"\xc3":
        raise ValueError("Runtime-class accessor is outside the exact pinned direct-return profile")
    descriptor = get_class + 7 + struct.unpack("<i", code[3:7])[0]
    raw = image.get_data(descriptor - base, 32)
    label, size, schema, create, parent = struct.unpack("<QIIQQ", raw)
    class_name = image.get_string_at_rva(label - base, 512).decode("ascii")
    if not class_name or len(class_name) >= 512:
        raise ValueError("Invalid runtime class name")
    function = next((entry.struct for entry in image.DIRECTORY_ENTRY_EXCEPTION
                     if entry.struct.BeginAddress == create - base), None)
    create_extent = None
    if function is not None:
        create_extent = {"start": hex(base + function.BeginAddress), "end_exclusive": hex(base + function.EndAddress),
                         "sha256": digest(image.get_data(function.BeginAddress, function.EndAddress - function.BeginAddress))}
    return {"rtti_class": name, "vtable": hex(vtable), "serializer": row["serialize_addr"],
            "get_runtime_class": hex(get_class), "accessor_sha256": digest(code),
            "runtime_descriptor": hex(descriptor), "runtime_descriptor_sha256": digest(raw),
            "published_archive_class": class_name, "same_as_rtti_name": class_name == name,
            "runtime_object_size": size, "runtime_schema_word": hex(schema),
            "create_object": hex(create), "get_base_class": hex(parent), "create_object_extent": create_extent}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("module", type=Path)
    parser.add_argument("serialize_map", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--archive-module", type=Path, required=True)
    args = parser.parse_args()
    data = args.module.read_bytes()
    if digest(data) != MODEL_SHA256:
        raise ValueError("Runtime-class publication requires the exact pinned 2026 model module")
    image = pefile.PE(data=data)
    archive_data = args.archive_module.read_bytes()
    if digest(archive_data) != ARCHIVE_SHA256:
        raise ValueError("Runtime publication dispatch requires the exact pinned archive module")
    archive = pefile.PE(data=archive_data)
    archive_base = archive.OPTIONAL_HEADER.ImageBase
    lookup = archive.get_data(0x31A3AA1B - archive_base, 19)
    if lookup[6:8] != b"\xff\x10" or lookup[14:15] != b"\xe8":
        raise ValueError("Native class dispatch differs from the pinned slot-zero lookup")
    target = 0x31A3AA29 + 5 + struct.unpack("<i", lookup[15:19])[0]
    if target != 0x31A3A850:
        raise ValueError("Native class publication no longer calls the pinned WriteClass")
    mapping = json.loads(args.serialize_map.read_bytes())
    result = {"schema": "kit.sw2026.reference-plane-runtime-publication.v1", "tool_sha256": digest(Path(__file__).read_bytes()),
              "module_sha256": MODEL_SHA256, "image_base": hex(image.OPTIONAL_HEADER.ImageBase),
              "serialize_map_sha256": digest(args.serialize_map.read_bytes()),
              "archive_dispatch": {"module_sha256": ARCHIVE_SHA256, "write_object": "0x31a3a930",
                                   "runtime_class_virtual_slot": 0, "runtime_class_lookup_call": "0x31a3aa21",
                                   "write_class_call": "0x31a3aa29", "write_class_target": hex(target),
                                   "dispatch_window_sha256": digest(lookup)},
              "classes": [publication(image, name, mapping[name]) for name in CLASSES],
              "native_model_sources_read": 0, "native_processes_started": 0, "writer_output_count": 0,
              "vendor_code_emitted": False, "source_correlation_qualified": False, "native_acceptance": False}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sha256": digest(args.output.read_bytes()), "classes": len(CLASSES), "vendor_code_emitted": False}))


if __name__ == "__main__":
    main()
