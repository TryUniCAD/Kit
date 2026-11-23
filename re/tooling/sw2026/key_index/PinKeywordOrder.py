from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent.parent))
from InspectPartEnvironmentSource import Image


MODULES = {
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    "sldmfcu.dll": "af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def cell(image, table, slot, target):
    address = table + slot
    actual, = unpack("<Q", image.read(address, address + 8))
    require(actual == target, "native keyword virtual cell changed")
    return {"table": hex(table), "slot": hex(slot), "target": hex(actual)}


def instructions(image, address, encoding):
    actual = bytes.fromhex(encoding)
    require(image.read(address, address + len(actual)) == actual, "keyword dataflow changed")


def span(image, start, end):
    return {"address": hex(start), "end_exclusive": hex(end),
            "sha256": sha256(image.read(start, end)).hexdigest()}


def inspect(bin_directory):
    model, mfc = (Image(bin_directory / name, digest) for name, digest in MODULES.items())
    feature_cells = {
        name: [cell(model, table, 0x1b00, 0x4bb2aa60), cell(model, table, 0x1398, target)]
        for name, table, target in (
            ("profile", 0x4d0e8e80, 0x4c0d7a70), ("extrude", 0x4cf3d488, 0x4bae0010),
            ("cut", 0x4cf4e530, 0x4bae0010), ("revolve", 0x4d185908, 0x4c396c00),
        )
    }
    display_cells = {
        name: cell(model, table, 0x498, 0x4c837780)
        for name, table in (("distance", 0x4d253270), ("radial", 0x4d255be0), ("angular", 0x4d247828))
    }
    parameter_cells = {
        name: cell(model, table, 0x188, 0x4b283ba0)
        for name, table in (("length", 0x4d123bf0), ("angle", 0x4d124128))
    }
    checks = (
        (0x4c8377a8, "4c8be1"),
        (0x4c83784f, "4c8bf8"),
        (0x4c8379c8, "4d85ff7420"),
        (0x4c8379d3, "ff908801000083f8ff740f"),
        (0x4c8379e4, "ff9088010000448be0"),
        (0x4c8379ed, "498d4d18458bc4"),
        (0x4b283ba0, "8b4108c3"),
        (0x4bb2aaa4, "ff9098130000"),
        (0x4bb2aac9, "ff9098040000"),
    )
    for address, encoding in checks:
        instructions(model, address, encoding)
    key_format = model.read(0x4cda0628, 0x4cda0634).decode("utf-16-le").rstrip("\0")
    require(key_format == "@@@%d", "native keyword discriminator grammar changed")
    imports = model.imports()
    selected = {
        key: imports[key] for key in ("0x4cd31978", "0x4cd31980", "0x4cd33c28", "0x4cd33c40",
                                      "0x4cd33d78", "0x4cd3da80")
    }
    require(selected["0x4cd33c28"]["name"].startswith("?UpdateNodeValue@moXmlDataExtracter_c@@")
            and selected["0x4cd33c40"]["name"].startswith("?UpdateUserName@moXmlDataExtracter_c@@")
            and selected["0x4cd31978"]["name"].startswith("?UpdateFromMapAndGetXmlDoc@moXmlDataExtracter_c@@"),
            "keyword descriptor no longer feeds the xml extractor")
    store = cell(mfc, 0x3cca30d0, 0x68, 0x3c979630)
    finish = cell(mfc, 0x3cca30d0, 0x30, 0x3c979c90)
    return {"schema": "kit.sw2026.keyword-order-native.v1", "oracle_build": "34.5.2.0604",
            "modules": MODULES, "feature_cells": feature_cells, "display_cells": display_cells,
            "parameter_cells": parameter_cells, "keyword_imports": selected,
            "store_map": {"setter": store, "materializer": finish},
            "dimension_key_format": key_format, "no_parameter_id_uses_display_pointer_low32": True,
            "module_spans": {
                "sldmodu.dll": [span(model, 0x4bb2aa60, 0x4bb2aaf1),
                                span(model, 0x4c837780, 0x4c837a93),
                                span(model, 0x4c499740, 0x4c499764),
                                span(model, 0x4bae0010, 0x4bae0123)],
                "sldmfcu.dll": [span(mfc, 0x3c979630, 0x3c979663),
                                span(mfc, 0x3c9798a0, 0x3c979908),
                                span(mfc, 0x3c979c90, 0x3c97a110)],
            },
            "script_sha256": sha256(HERE.read_bytes()).hexdigest(),
            "native_execution": False, "heldout_inputs_read": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("module_directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    receipt = (json.dumps(inspect(args.module_directory), indent=2, sort_keys=True) + "\n").encode()
    with args.output.open("xb") as target:
        target.write(receipt)
    print(json.dumps({"sha256": sha256(receipt).hexdigest(), "native_modules": len(MODULES)}))
