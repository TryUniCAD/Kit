import argparse
from hashlib import sha256
import importlib.metadata
import importlib.util
import json
from math import cos, isfinite, sin, sqrt
from pathlib import Path
from struct import pack, unpack_from
import sys


def require(value, reason):
    if not value:
        raise ValueError(reason)


def digest(value):
    return sha256(value).hexdigest()


def dependency(root, relative, expected):
    path = root / relative
    require(digest(path.read_bytes()) == expected, "source evidence dependency differs")
    spec = importlib.util.spec_from_file_location("angle_api_" + path.stem, path)
    require(
        spec is not None and spec.loader is not None, "evidence dependency is absent"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def integer(item):
    name = item.opcode.name
    if name == "ldc.i4.m1":
        return -1
    if name in ("ldc.i4", "ldc.i4.s"):
        return int(item.operand)
    if name.startswith("ldc.i4."):
        return int(name.rsplit(".", 1)[1])
    raise ValueError("the selected instruction is not an integer literal")


def sites(body, token):
    return [
        ordinal
        for ordinal, item in enumerate(body.instructions)
        if item.opcode.name in ("call", "callvirt", "newobj")
        and item.operand.value == token
    ]


def managed_check(readers, bodies):
    body = bodies["apicoupleru.dll"][0x06001553]
    prefix = [item.opcode.name for item in body.instructions[:5]]
    require(
        prefix == ["ldarg.3", "ldc.i4.8", "shr.un", "ldc.i4.1", "and"],
        "the actual option-flip extraction differs",
    )
    constraints = {}
    for token, name in ((0x0A0000A7, "coincident"), (0x0A0000A9, "angle")):
        indexes = sites(body, token)
        require(len(indexes) == 1, "the ordinary constraint has ambiguous construction")
        selected = None
        for ordinal in range(indexes[0] - 1, -1, -1):
            item = body.instructions[ordinal]
            if item.opcode.name == "and":
                selected = integer(body.instructions[ordinal - 1])
                break
        constraints[name] = selected
    require(constraints == {"coincident": 4, "angle": 16}, "constraint bits differ")
    packet = bodies["apicoupleru.dll"][0x06001551]
    marks = [
        integer(item)
        for item in packet.instructions
        if item.opcode.name.startswith("ldc.i4")
    ]
    require(
        all(value in marks for value in (0, 1, 2, 3)), "selection-mark bounds differ"
    )
    require(len(sites(packet, 0x06001553)) == 3, "the ordered triplet is not preserved")
    require(
        len(sites(packet, 0x060013BE)) == 1, "actual selection marks are not queried"
    )
    require(
        len(sites(packet, 0x0A0000B7)) == 1, "the current API flag is not published"
    )
    old = bodies["sldcoreu.dll"][0x06004DE1]
    names = [
        readers["sldcoreu.dll"].token(item.operand.value).get("name")
        for item in old.instructions
        if item.opcode.name in ("call", "callvirt")
    ]
    require(
        "moRefPlnData_c.isCreatedByOldAPI_0" in names
        and "get_IsBeingCreatedByAPI" not in names,
        "old API and current command state are no longer separate",
    )
    return {
        "constraint_bits": constraints,
        "flip_bit": 1 << integer(body.instructions[1]),
        "ordered_geometry_slots": 3,
        "selection_mark_is_queried": True,
        "current_api_flag_is_not_old_api_predicate": True,
    }


def numeric_case(case):
    angle = case["angle_rad"]
    require(
        isinstance(angle, (int, float))
        and isfinite(angle)
        and 0 < angle < 1.5707963267948966,
        "the numeric experiment requires an ordinary finite acute angle",
    )
    require(type(case["flip"]) is bool, "the ordinary flip input must be boolean")
    selected = {}
    for item in case["selection_append_order"]:
        mark = item["mark"]
        require(type(mark) is int and mark in (0, 1), "unsupported selection mark")
        require(mark not in selected, "duplicate ordinary selection mark")
        selected[mark] = item
    require(
        set(selected) == {0, 1}
        and selected[0]["kind"] == "plane"
        and selected[1]["kind"] == "line",
        "the experiment needs the real selected plane and hinge line",
    )
    normal = case["analytic_base_normal"]
    hinge = case["analytic_hinge_unit"]
    require(len(normal) == len(hinge) == 3, "analytic frame is malformed")
    require(
        all(isfinite(value) for value in normal + hinge),
        "nonfinite analytic coordinates",
    )
    require(
        abs(sum(a * b for a, b in zip(normal, hinge))) < 1e-14, "hinge is not in plane"
    )
    cross = [
        hinge[1] * normal[2] - hinge[2] * normal[1],
        hinge[2] * normal[0] - hinge[0] * normal[2],
        hinge[0] * normal[1] - hinge[1] * normal[0],
    ]
    signed = -angle if case["flip"] else angle
    rotated = [
        value * cos(signed) + delta * sin(signed) for value, delta in zip(normal, cross)
    ]
    require(
        abs(sqrt(sum(value * value for value in rotated)) - 1) < 1e-14,
        "analytic rotation failed",
    )
    edit = case["edit_angle_rad"]
    require(
        isfinite(edit) and 0 < edit < 1.5707963267948966,
        "the edit needs an ordinary acute angle",
    )
    edited = -edit if case["flip"] else edit
    edited_normal = [
        value * cos(edited) + delta * sin(edited) for value, delta in zip(normal, cross)
    ]
    constraint = 16 | (256 if case["flip"] else 0)
    return {
        "case": case["id"],
        "api_arguments": [constraint, angle, 4, 0.0, 0, 0.0],
        "ordered_geometry": [
            {
                "slot": 0,
                "kind": "AngleGeom_c",
                "reference": selected[0]["identity"],
                "angle_rad": angle,
                "reverse": case["flip"],
                "count": 1,
            },
            {
                "slot": 1,
                "kind": "CoincidentGeom_c",
                "reference": selected[1]["identity"],
            },
            None,
        ],
        "angle_ieee_le": pack("<d", angle).hex(),
        "independent_right_handed_normal": rotated,
        "edit_angle_rad": edit,
        "independent_edit_right_handed_normal": edited_normal,
        "native_direction_sign_verified": False,
    }


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "evidence output must be unused")
    source = args.knowledge.read_bytes()
    knowledge = json.loads(source)
    require(
        knowledge["schema"] == "kit.sw2026.cylinder-angle-api.v1",
        "knowledge schema differs",
    )
    require(
        knowledge["document_version"] == 19000,
        "this pin requires document version 19000",
    )
    modules = {
        name: dependency(args.root, name, expected)
        for name, expected in knowledge["dependencies"].items()
    }
    pe = modules["re/tooling/sw2026/freecad_cylinder/NativeNamePe.py"].NativeNamePe
    native = modules["re/tooling/sw2026/freecad_cylinder/PinCylinderDirectionWire.py"]
    managed = modules["re/tooling/sw2026/ManagedConstructionIndex.py"]
    require(
        {name: importlib.metadata.version(name) for name in managed.PARSER_VERSIONS}
        == managed.PARSER_VERSIONS,
        "managed parser identity differs",
    )
    images, groups = {}, {}
    for name, expected in knowledge["modules"].items():
        image = pe((args.inputs / name).read_bytes())
        require(
            image.sha256 == expected["sha256"]
            and len(image.data) == expected["bytes"]
            and hex(image.base) == expected["base"]
            and hex(image.machine) == expected["machine"],
            "licensed original module identity differs",
        )
        images[name] = image
        groups[name] = native.unwind_groups(image)
    functions = []
    for row in knowledge["native_functions"]:
        expected = {
            key: value for key, value in row.items() if key not in ("module", "key")
        }
        observed = native.pin_function(
            images[row["module"]], expected["entry"], *groups[row["module"]]
        )
        require(
            observed == expected, "whole native function or unwind fragment differs"
        )
        functions.append({"key": row["key"], "module": row["module"], **observed})
    for row in knowledge["qwords"]:
        image = images[row["module"]]
        offset = image.offset(int(row["address"], 16) - image.base, 8)
        require(
            hex(unpack_from("<Q", image.data, offset)[0]) == row["value"],
            "vtable or CLR fixup differs",
        )
    for row in knowledge["spans"]:
        image = images[row["module"]]
        offset = image.offset(int(row["address"], 16) - image.base, row["bytes"])
        require(
            digest(image.data[offset : offset + row["bytes"]]) == row["sha256"],
            "native bridge differs",
        )
    readers, bodies, methods = {}, {}, {}
    for name, expected in knowledge["managed"].items():
        reader = managed.ManagedIndex(
            args.inputs / name, knowledge["modules"][name]["sha256"], None, None
        )
        identity = reader.receipt([], False)["module"]
        require(
            identity["mvid"] == expected["mvid"]
            and identity["cli_flags"] == expected["cli_flags"],
            "CLI identity differs",
        )
        readers[name], bodies[name], methods[name] = reader, {}, []
        for row in expected["methods"]:
            token = int(row["token"], 16)
            observed = reader.method(token)
            require(observed == row, "complete managed method identity differs")
            require(
                observed["managed"] and observed["cil"] and not observed["native"],
                "native method is not CIL",
            )
            definition = reader.image.net.mdtables.MethodDef.rows[
                (token & 0xFFFFFF) - 1
            ]
            bodies[name][token] = managed.CilMethodBody(
                managed.CilMethodBodyReaderBytes(
                    reader.image.get_data(definition.Rva, 1 << 20)
                )
            )
            methods[name].append(observed)
    rules = managed_check(readers, bodies)
    raw = args.protocol.read_bytes()
    protocol = json.loads(raw)
    require(
        protocol["schema"] == "kit.sw2026.angular-plane-author-protocol.v1",
        "protocol schema differs",
    )
    require(
        len(protocol["disclosed_numeric_cases"]) == 2,
        "protocol pins exactly two authored numeric cases",
    )
    numeric = [numeric_case(case) for case in protocol["disclosed_numeric_cases"]]
    result = {
        "schema": "kit.sw2026.cylinder-angle-api-pin.v1",
        "document_version": 19000,
        "tool_sha256": digest(Path(__file__).read_bytes()),
        "knowledge_sha256": digest(source),
        "protocol_sha256": digest(raw),
        "modules": knowledge["modules"],
        "native_functions": functions,
        "managed_methods": methods,
        "verified_slots": knowledge["qwords"],
        "verified_spans": knowledge["spans"],
        "extracted_managed_rules": rules,
        "authored_numeric_cases": numeric,
        "native_function_bytes": sum(row["total_bytes"] for row in functions),
        "managed_code_bytes": sum(
            row["code_bytes"] for values in methods.values() for row in values
        ),
        "limits": knowledge["limits"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "output_sha256": digest(args.output.read_bytes()),
                "native_functions": len(functions),
                "managed_methods": sum(len(rows) for rows in methods.values()),
                "native_acceptance": False,
                "writer_outputs": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
