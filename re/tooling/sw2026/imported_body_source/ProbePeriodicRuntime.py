from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import platform
from struct import pack
import zlib

from SealedCylinderModel import geometry_document
from VerifyPublicCyl import EPOCH, NATIVE_IDENTITY, SPEC, guarded_prepare, warm
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


CONFIG = "Contents/Config-0"
HEADER = "Contents/Config-0-ModelHeader"


def digest(data):
    return [len(data), sha256(data).hexdigest()]


def build():
    warm()
    return guarded_prepare(
        geometry_document(SPEC),
        Path("/unused-periodic-stage/TranslatedZ.SLDPRT"),
        EPOCH,
        WriteOptions(values={"final_destination": NATIVE_IDENTITY}),
    )


def capture(output):
    generated = build()
    platform_name = platform.system()
    data = {
        "container": digest(generated.BytesValue),
        "runtime": platform.python_version(),
        "streams": {
            name: digest(stream) for name, stream in sorted(generated.StreamsValue.items())
        },
        "zlib": zlib.ZLIB_RUNTIME_VERSION,
    }
    output.mkdir(exist_ok=True)
    with (output / (platform_name + "Config.bin")).open("xb") as stream:
        stream.write(generated.StreamsValue[CONFIG])
    filename = "MacLogical.json" if platform_name == "Darwin" else platform_name + "Logical.json"
    with (output / filename).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, sort_keys=True)
    return data


def views(data, header_data):
    model = ReadConfigMut(data, 19000, ReadHeaderGraph(header_data, 19000))
    matrices = {}
    for entry in model.MapValue.EntriesValue:
        node = entry.EntryValue
        if not isinstance(node, ArchiveNode) or node.ClassValue.NameValue != "moView_c":
            continue
        fields = node.FieldsValue
        matrix = fields["f368"].get("f08")
        if matrix:
            raw = pack("<9d", *(matrix[f"m{index}"] for index in range(9)))
            begin = data.index(raw, node.StartOffset, node.EndOffset)
            matrices[fields["f358"]] = (begin, matrix)
    return matrices


def compare(packet):
    generated = build()
    mac, windows = (
        (packet / (platform_name + "Config.bin")).read_bytes()
        for platform_name in ("Darwin", "Windows")
    )
    if mac != generated.StreamsValue[CONFIG]:
        raise ValueError("macOS typed reference changed")
    metadata = [
        json.loads((packet / (platform_name + "Logical.json")).read_bytes())
        for platform_name in ("Mac", "Windows")
    ]
    prior, later = (item["streams"] for item in metadata)
    changed = sorted(name for name in prior.keys() | later.keys() if prior.get(name) != later.get(name))
    if changed != [CONFIG] or [prior[CONFIG], later[CONFIG]] != [digest(mac), digest(windows)]:
        raise ValueError("runtime contrast changed more than the declared configuration")
    trees = [views(data, generated.StreamsValue[HEADER]) for data in (mac, windows)]
    changes, covered = [], set()
    if trees[0].keys() != trees[1].keys():
        raise ValueError("standard view inventory changed")
    for name, (start, matrix) in trees[0].items():
        other_start, other = trees[1][name]
        if start != other_start:
            raise ValueError("standard view wire span moved")
        for index in range(9):
            field = f"m{index}"
            before, after = matrix[field], other[field]
            if pack("<d", before) == pack("<d", after):
                continue
            offset = start + index * 8
            covered.update(range(offset, offset + 8))
            changes.append(
                {"view": name, "field": "f368.f08." + field, "wire_offset": offset,
                 "mac_hex": before.hex(), "windows_hex": after.hex()}
            )
    differing = {offset for offset, (first, second) in enumerate(zip(mac, windows, strict=True)) if first != second}
    if len(changes) != 8 or len(differing) != 56 or not differing <= covered:
        raise ValueError("unexpected arithmetic or other serialized field variation")
    return {
        "schema": "kit.sw2026.public-periodic-runtime-arithmetic.v1",
        "case": "disclosed TranslatedZ",
        "epoch": EPOCH,
        "logical_destination": NATIVE_IDENTITY,
        "runtime_builds": metadata,
        "changed_streams": changed,
        "only_wire_delta": changes,
        "different_wire_bytes": len(differing),
        "public_native_geometry_credit": 0,
    }


def main():
    parser = ArgumentParser(description="Trace cross-runtime differences in a generated periodic part")
    parser.add_argument("mode", choices=("capture", "compare"))
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    method = capture if args.mode == "capture" else compare
    print(json.dumps(method(args.packet), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
