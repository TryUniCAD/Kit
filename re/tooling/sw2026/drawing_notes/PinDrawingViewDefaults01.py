from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
from struct import unpack
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "freecad_cylinder"))
from InspectPartEnvironmentSource import Image
from NativeNamePe import NativeNamePe


MODEL = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
RESOURCES = "531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111"
RESOURCE_EVIDENCE = "ev_0eeec8d0a893cc07b7a6d87c44e6d2ff034d00c266fbc6b4ef1de3c92f4a9a75"
VTABLE = 0x4D26AF68


def require(condition, message):
    if not condition:
        raise ValueError(message)


def span(image, name, start, end):
    raw = image.read(start, end)
    return {
        "name": name, "module": "sldmodu.dll", "start": hex(start),
        "end_exclusive": hex(end), "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
    }


def function(image, name, address, leaf_end=None):
    candidates = [row for row in image.functions if row[0] <= address - image.base < row[1]]
    if leaf_end is not None:
        require(not candidates, "leaf is part of an exception group")
        return {**span(image, name, address, leaf_end), "unwind_fragments": []}
    require(len(candidates) == 1, "ambiguous native function address")
    root = image.root(candidates[0])
    require(root[0] + image.base == address, "selected entry is not the actual unwind root")
    parts = sorted(row for row in image.functions if image.root(row) == root)
    body = span(image, name, address, image.base + parts[-1][1])
    body["unwind_fragments"] = [
        {**span(image, name, image.base + begin, image.base + end), "unwind_rva": hex(unwind)}
        for begin, end, unwind in parts
    ]
    image.verify_function(body)
    return body


def cell(image, offset, wanted):
    address = VTABLE + offset
    actual, = unpack("<Q", image.read(address, address + 8))
    require(actual == wanted, "drawing virtual cell changed")
    return {"module": "sldmodu.dll", "cell": hex(address), "target": hex(actual), "offset": hex(offset)}


def relative(image, address, opcode, length, expected):
    data = image.read(address, address + length)
    displacement, = unpack("<i", data[-4:])
    require(data.startswith(opcode) and address + length + displacement == expected,
            "drawing view instruction target changed")


def main():
    parser = ArgumentParser()
    parser.add_argument("--bin-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    image = Image(args.bin_directory / "sldmodu.dll", MODEL)
    resource = NativeNamePe((args.bin_directory / "sldresu.dll").read_bytes())
    require(resource.sha256 == RESOURCES, "original drawing label resource changed")
    label, = resource.resource(0x2ABC)
    require(label["language_id"] == 1033 and label["value"] == "*Full Sheet",
            "native full sheet resource differs")
    require(image.read(0x4D26C9C8, 0x4D26C9D6).decode("utf-16le") == "Unused\0",
            "native unused view label differs")
    lookup, = unpack("<Q", image.read(VTABLE - 8, VTABLE))
    record = unpack("<IIIIII", image.read(lookup, lookup + 24))
    type_name = image.base + record[3] + 16
    drawing_type = b".?AVmoDrawing_c@@\0"
    require(image.read(type_name, type_name + len(drawing_type)) == drawing_type,
            "drawing vtable RTTI type changed")
    relative(image, 0x4C96B4FE, b"\x48\x8d\x05", 7, VTABLE)
    relative(image, 0x4C96B962, b"\xe8", 5, 0x4C14FB90)
    relative(image, 0x4C96B9B0, b"\xe8", 5, 0x4C14FB90)
    relative(image, 0x4C96B973, b"\x48\x8d\x15", 7, 0x4D26C9C8)
    relative(image, 0x4C97AE92, b"\x48\x8d\x15", 7, 0x4D26C9C8)
    relative(image, 0x4C97AF26, b"\xe8", 5, 0x4C150C70)
    relative(image, 0x4C97AF37, b"\xe8", 5, 0x4C150C80)
    require(image.read(0x4C96B932, 0x4C96B937) == b"\xba\xbc\x2a\x00\x00"
            and image.read(0x4C96B9C3, 0x4C96B9C6) == b"\x83\xfb\x0a",
            "drawing indexed view allocation changed")
    result = {
        "schema": "kit.sw2026.drawing-default-view-native.v1",
        "oracle_build": "34.5.2.0604",
        "modules": [{"name": "sldmodu.dll", "sha256": MODEL}],
        "resource": {"module": "sldresu.dll", "sha256": RESOURCES, "rea_evidence": RESOURCE_EVIDENCE, **label},
        "functions": [
            function(image, name, start, end) for name, start, end in (
                ("DrawingConstructor", 0x4C96B480, None),
                ("DrawingRefreshViewNames", 0x4C97AE50, None),
                ("DrawingRefreshFirstViewTransforms", 0x4C97AEF0, None),
                ("IndexedViewConstructor", 0x4C14FB90, None),
                ("ModelDefaultViewsDispatch", 0x4C0352C0, None),
                ("ModelSerializer", 0x4C234150, None),
                ("SetModelToViewTransform", 0x4C150C70, 0x4C150C7E),
                ("SetPanZoomTransform", 0x4C150C80, 0x4C150C8E),
            )
        ],
        "instruction_windows": [
            span(image, "ConstructNamedDrawingViews", 0x4C96B91B, 0x4C96B9DC),
            span(image, "InstallActualDrawingVtable", 0x4C96B4FE, 0x4C96B508),
        ],
        "data_windows": [
            span(image, "DrawingCompleteObjectLocator", lookup, lookup + 24),
            span(image, "DrawingRttiName", type_name, type_name + len(drawing_type)),
            span(image, "UnusedLiteral", 0x4D26C9C8, 0x4D26C9D6),
        ],
        "vtable_cells": [cell(image, 0x1880, 0x4C97AE50), cell(image, 0x15D0, 0x4C97AEF0)],
        "imports": [],
        "verified": True,
        "cad_executed": False,
        "heldout_source_reads": 0,
    }
    imports = image.imports()
    for address in ("0x4cd34e70", "0x4cd34ea0", "0x4cd34ea8", "0x4cd3a658", "0x4cd3a668"):
        result["imports"].append({"source_module": "sldmodu.dll", "iat": address, **imports[address]})
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        out.write(dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
