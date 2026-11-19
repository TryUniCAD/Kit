import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import struct
import sys

MODULES = {
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    "sldmgu.dll": "99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c",
}
HELPERS = {
    "NativeNamePe.py": "e07df1c6b1b16fa3958f1db4adac95b16ebc30888340b33238e4a9703d8a89c7",
    "PinCylinderDirectionWire.py": "8e212ceb466a119e5b8445b814221cde8f81c4632f0bc7ce23d7bf420d9434d7",
}
FUNCTIONS = (
    ("axis_constructor", "sldmodu.dll", "0x4c281520", None),
    ("axis_update", "sldmodu.dll", "0x4c288230", None),
    ("axis_intersection", "sldmodu.dll", "0x4c286ca0", None),
    ("axis_plane_owner", "sldmodu.dll", "0x4c289c20", None),
    ("angle_geometry_constructor", "sldmodu.dll", "0x4c2d77a0", None),
    ("angle_normal", "sldmodu.dll", "0x4b8ee700", None),
    ("angle_reverse", "sldmodu.dll", "0x4b2b1c70", 5),
    ("angle_magnitude", "sldmodu.dll", "0x4b2bd110", 6),
    ("angle_plane", "sldmodu.dll", "0x4b8ef160", None),
    ("concrete_plane_update", "sldmodu.dll", "0x4b8e8dd0", None),
    ("plane_intersection", "sldmgu.dll", "0x31e0bd50", None),
    ("cross_product", "sldmgu.dll", "0x31f1a050", None),
    ("rotation_xform", "sldmgu.dll", "0x31f24670", None),
    ("rotation_matrix", "sldmgu.dll", "0x31e2cd80", None),
    ("unit_vector_xform", "sldmgu.dll", "0x31f19400", None),
    ("vector_matrix", "sldmgu.dll", "0x31f1a0d0", None),
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def load(path, expected, name):
    require(
        path.is_file()
        and not path.is_symlink()
        and sha256(path.read_bytes()).hexdigest() == expected,
        "independent source helper identity differs: " + name,
    )
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "helper cannot load")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pin(root, originals):
    source = root / "re/tooling/sw2026/freecad_cylinder"
    native = load(
        source / "NativeNamePe.py", HELPERS["NativeNamePe.py"], "native_sign_pe"
    )
    sys.path.insert(0, str(source))
    tooling = load(
        source / "PinCylinderDirectionWire.py",
        HELPERS["PinCylinderDirectionWire.py"],
        "native_sign_pin",
    )
    images = {}
    groups = {}
    for name, expected in MODULES.items():
        image = native.NativeNamePe((originals / name).read_bytes())
        require(
            image.sha256 == expected, "original exact-build module differs: " + name
        )
        images[name] = image
        groups[name] = tooling.unwind_groups(image)
    rows = [
        {
            "role": role,
            "module": name,
            **tooling.pin_function(images[name], address, *groups[name], leaf),
        }
        for role, name, address, leaf in FUNCTIONS
    ]
    model = images["sldmodu.dll"]
    imports = model.imports()
    imported = {
        "plane_intersection": 0x4CD3C030,
        "rotate_xform": 0x4CD3ABC0,
        "unit_vector_xform": 0x4CD3A988,
    }
    expected_names = {
        "plane_intersection": "?interLine@@YAHAEBVmgPlane_c@@0PEAVmgPoint_c@@PEAVmgUnitVector_c@@@Z",
        "rotate_xform": "?mg_RotateXform@@YA?AVmgXform_c@@NAEBVmgVector_c@@N@Z",
        "unit_vector_xform": "??D@YA?AVmgUnitVector_c@@AEBV0@AEBVmgXform_c@@@Z",
    }
    for role, address in imported.items():
        require(
            imports[address]["module"] == "sldmgu.dll"
            and imports[address]["name"] == expected_names[role],
            "actual model import differs: " + role,
        )
    slots = []
    for vtable, slot, target in (
        (0x4D162258, 0x90, 0x4C286CA0),
        (0x4CED1C20, 0x238, 0x4B8E8DD0),
    ):
        actual = struct.unpack_from(
            "<Q", model.data, model.offset(vtable - model.base + slot, 8)
        )[0]
        require(actual == target, "actual concrete virtual slot differs")
        slots.append({"vtable": hex(vtable), "slot": hex(slot), "target": hex(actual)})
    mask = model.data[model.offset(0x4CD9E340 - model.base, 16) :][:16]
    require(
        struct.unpack_from("<Q", mask)[0] == 0x8000000000000000,
        "angle sign mask differs",
    )
    return {
        "schema": "kit.sw2026.oblique-cylinder-native-sign-pin.v1",
        "modules_sha256": MODULES,
        "source_helpers_sha256": HELPERS,
        "functions": rows,
        "function_count": len(rows),
        "total_code_bytes": sum(row["total_bytes"] for row in rows),
        "virtual_slots": slots,
        "imports": {
            role: {"iat": hex(address), **imports[address]}
            for role, address in imported.items()
        },
        "angle_sign_mask": {
            "address": "0x4cd9e340",
            "bytes": 16,
            "sha256": sha256(mask).hexdigest(),
        },
        "construction_rules": {
            "axis_order": "constructor f80=first actual plane, f88=second actual plane; intersection consumes this order",
            "axis_direction": "unit(cross(first_plane_normal, second_plane_normal))",
            "angle": "actual angle geometry f38, negated when byte f40 is true",
            "ordinary_perpendicular_hinge": "actual base-plane normal rotated about actual directed line with that signed angle; the non-perpendicular correction remains a distinct branch",
            "api_selection_to_native_owner_order": "not generalized by this static packet; measured D01 reverses the two principal-plane selections and the new probe checks actual directed hinges",
        },
        "native_launches": 0,
        "writer_output_count": 0,
        "heldout_reads": 0,
        "native_acceptance": False,
    }


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--originals", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        not args.output.exists() and args.output.parent.is_dir(), "choose unused output"
    )
    result = pin(args.root.resolve(), args.originals.resolve())
    args.output.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "passed": True,
                "function_count": result["function_count"],
                "total_code_bytes": result["total_code_bytes"],
                "output_sha256": sha256(args.output.read_bytes()).hexdigest(),
                "native_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
