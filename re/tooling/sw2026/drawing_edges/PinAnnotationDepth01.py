import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from struct import unpack_from
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def source(root, name, expected):
    path = root / name
    require(digest(path) == expected, "source-pin helper differs")
    spec = importlib.util.spec_from_file_location("annotation_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--originals", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "pin receipt must be unused")
    knowledge = json.loads(args.knowledge.read_bytes())
    loaded = {
        name: source(args.root, name, expected)
        for name, expected in knowledge["dependencies"].items()
    }
    pe = loaded["re/tooling/sw2026/freecad_cylinder/NativeNamePe.py"].NativeNamePe
    native = loaded["re/tooling/sw2026/freecad_cylinder/PinCylinderDirectionWire.py"]
    images, groups = {}, {}
    for name, expected in knowledge["modules"].items():
        image = pe((args.originals / name).read_bytes())
        require(
            image.sha256 == expected["sha256"]
            and len(image.data) == expected["bytes"]
            and hex(image.base) == expected["base"],
            "licensed original identity differs",
        )
        images[name] = image
        groups[name] = native.unwind_groups(image)
    functions = []
    for row in knowledge["functions"]:
        actual = native.pin_function(
            images[row["module"]],
            row["pin"]["entry"],
            *groups[row["module"]],
            leaf_bytes=row.get("leaf_bytes")
        )
        require(actual == row["pin"], "whole native function differs")
        functions.append({"key": row["key"], "module": row["module"], "pin": actual})
    for row in knowledge["vtable_cells"]:
        image = images[row["module"]]
        actual = unpack_from(
            "<Q", image.data, image.offset(int(row["address"], 16) - image.base, 8)
        )[0]
        require(hex(actual) == row["target"], "annotation vtable binding differs")
    calls = []
    for row in knowledge["critical_calls"]:
        calls.append(
            native.pin_call(
                images[row["module"]],
                {k: value for k, value in row.items() if k != "module"},
            )
        )
    result = {
        "schema": "kit.sw2026.annotation-depth-source-pin.v1",
        "passed": True,
        "knowledge_sha256": digest(args.knowledge),
        "modules": knowledge["modules"],
        "functions": functions,
        "critical_calls": calls,
        "vtable_cells": knowledge["vtable_cells"],
        "rules": knowledge["rules"],
        "vendor_code_executed": False,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
    }
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "sha256": digest(args.output),
                "functions": len(functions),
                "vendor_code_executed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
