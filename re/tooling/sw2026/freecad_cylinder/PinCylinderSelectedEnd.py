import argparse
from hashlib import sha256
import importlib.metadata
import importlib.util
import json
from pathlib import Path
from struct import unpack_from
import sys


def require(value, reason):
    if not value:
        raise ValueError(reason)


def digest(value):
    return sha256(value).hexdigest()


def load_module(root, relative, expected, name):
    path = root / relative
    require(digest(path.read_bytes()) == expected, "shared evidence dependency differs")
    spec = importlib.util.spec_from_file_location(name, path)
    require(
        spec is not None and spec.loader is not None,
        "shared evidence module is unavailable",
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def integer(instruction):
    name = instruction.opcode.name
    if name == "ldc.i4.m1":
        return -1
    if name in ("ldc.i4", "ldc.i4.s"):
        return int(instruction.operand)
    if name.startswith("ldc.i4."):
        return int(name.rsplit(".", 1)[1])
    raise ValueError("the selected construction argument is not a literal integer")


def call_sites(body, token):
    return [
        index
        for index, instruction in enumerate(body.instructions)
        if instruction.opcode.name in ("call", "callvirt", "newobj")
        and instruction.operand.value == token
    ]


def type_argument(body):
    indexes = call_sites(body, 0x060044D8)
    require(len(indexes) == 1, "the concrete end does not publish one native type")
    index = indexes[0]
    require(
        body.instructions[index - 1].opcode.name == "call"
        and body.instructions[index - 1].operand.value == 0x0600505E
        and body.instructions[index - 2].opcode.name == "ldarg.0",
        "the native type argument no longer precedes the actual end index",
    )
    return integer(body.instructions[index - 3])


def construct_result(reader, body, destination):
    indexes = [
        index
        for index, item in enumerate(body.instructions)
        if item.offset == destination
    ]
    require(
        len(indexes) == 1, "the native-type switch destination is not an instruction"
    )
    selected = None
    for item in body.instructions[indexes[0] :]:
        if item.opcode.name == "newobj":
            require(selected is None, "one type branch creates multiple end packets")
            selected = reader.token(item.operand.value)["owner"]
        if item.opcode.name == "ret":
            return selected
    raise ValueError("the native-type branch has no bounded return")


def managed_rules(reader, bodies):
    surface = bodies[0x0600507E]
    reference = call_sites(surface, 0x060044EA)
    require(
        len(reference) == 1, "the surface end does not publish one selected reference"
    )
    clear = integer(surface.instructions[reference[0] - 1])
    shared = bodies[0x0600506A]
    constructor = call_sites(shared, 0x060044DF)
    require(
        len(constructor) == 1,
        "the base end does not create one selected-line direction",
    )
    direction_mode = integer(shared.instructions[constructor[0] - 1])
    switches = [
        item for item in bodies[0x0600503A].instructions if item.opcode.name == "switch"
    ]
    require(len(switches) == 1, "the current-end selector no longer has one switch")
    classes = {
        str(index): construct_result(reader, bodies[0x0600503A], destination)
        for index, destination in enumerate(switches[0].operand)
    }
    types = {
        reader.token(token)["owner"]: type_argument(bodies[token])
        for token in (
            0x06005072,
            0x06005078,
            0x0600507E,
            0x06005083,
            0x06005089,
            0x0600508C,
        )
    }
    end_indexes = []
    for token in (0x0600503D, 0x0600503F):
        body = bodies[token]
        setters = call_sites(body, 0x0600505D)
        require(len(setters) == 1, "the end packet does not bind one native end index")
        end_indexes.append(integer(body.instructions[setters[0] - 1]))
    result = {
        "native_type_by_concrete_packet": types,
        "current_packet_by_native_type": classes,
        "selected_surface_clear": clear,
        "selected_line_direction_mode": direction_mode,
        "end_index_order": end_indexes,
        "surface_direct_calls_set_distance": bool(call_sites(surface, 0x060044E7)),
        "base_direct_calls_set_distance": bool(call_sites(shared, 0x060044E7)),
        "surface_release_removes_reference": bool(
            call_sites(bodies[0x0600507C], 0x060044E9)
        ),
    }
    require(
        result["native_type_by_concrete_packet"]
        == {
            "BlindEndSpec_c": 0,
            "ToPointEndSpec_c": 3,
            "ToSurfaceEndSpec_c": 4,
            "OffsetFromSurfaceEndSpec_c": 5,
            "MidPlaneEndSpec_c": 6,
            "UpToBodyEndSpec_c": 7,
        },
        "the concrete native end publication changed",
    )
    require(
        clear == 1
        and direction_mode == 3
        and end_indexes == [0, 1]
        and not result["surface_direct_calls_set_distance"]
        and not result["base_direct_calls_set_distance"]
        and result["surface_release_removes_reference"],
        "selected end construction changed",
    )
    return result


def macro_map(images, selected):
    image = images[selected["module"]]
    site = int(selected["pointer_site"], 16)
    address = unpack_from("<Q", image.data, image.offset(site - image.base))[0]
    rows = []
    for index in range(128):
        values = unpack_from(
            "<5Q",
            image.data,
            image.offset(address - image.base) + index * selected["row_bytes"],
        )
        if values[1] == 0:
            break
        rows.append(
            {"ordinal": index, "kind": values[0], "owner_offset": hex(values[1])}
        )
    else:
        raise ValueError("the declared macro data map has no bounded sentinel")
    require(len(rows) == selected["expected_count"], "the macro data-map count changed")
    observed = [rows[row["ordinal"]] for row in selected["selected_rows"]]
    require(
        observed == selected["selected_rows"], "the ordered macro end-type rows changed"
    )
    return {
        "pointer_site": hex(site),
        "map_address": hex(address),
        "row_count": len(rows),
        "row_bytes": selected["row_bytes"],
        "end_type_rows": observed,
    }


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "the evidence output must be new")
    raw = args.knowledge.read_bytes()
    knowledge = json.loads(raw)
    require(
        knowledge["schema"] == "kit.sw2026.cylinder-selected-end.v1",
        "knowledge schema differs",
    )
    require(
        knowledge["document_version"] == 19000,
        "selected-end evidence requires version 19000",
    )
    modules = {}
    for relative, expected in knowledge["dependencies"].items():
        modules[relative] = load_module(
            args.root, relative, expected, "selected_" + Path(relative).stem
        )
    pe = modules["re/tooling/sw2026/freecad_cylinder/NativeNamePe.py"].NativeNamePe
    native = modules["re/tooling/sw2026/freecad_cylinder/PinCylinderDirectionWire.py"]
    managed = modules["re/tooling/sw2026/ManagedConstructionIndex.py"]
    versions = {
        name: importlib.metadata.version(name) for name in managed.PARSER_VERSIONS
    }
    require(versions == managed.PARSER_VERSIONS, "managed parser versions differ")
    images, exports, groups, identities = {}, {}, {}, []
    for name, expected in knowledge["modules"].items():
        image = pe((args.inputs / name).read_bytes())
        require(
            image.sha256 == expected["sha256"]
            and len(image.data) == expected["bytes"]
            and hex(image.base) == expected["base"]
            and hex(image.machine) == expected["machine"],
            "pinned selected-end original image differs",
        )
        images[name] = image
        exports[name] = native.exports(image)
        groups[name] = native.unwind_groups(image)
        identities.append(
            {
                "name": name,
                "sha256": image.sha256,
                "bytes": len(image.data),
                "base": hex(image.base),
                "parsed_export_count": len(exports[name]),
            }
        )
    reader = managed.ManagedIndex(
        args.inputs / "sldcoreu.dll",
        knowledge["modules"]["sldcoreu.dll"]["sha256"],
        None,
        None,
    )
    module = reader.receipt([], False)["module"]
    require(
        module["mvid"] == knowledge["managed"]["mvid"]
        and module["cli_flags"] == knowledge["managed"]["cli_flags"],
        "managed module identity differs",
    )
    bodies, methods = {}, []
    for expected in knowledge["managed"]["methods"]:
        token = int(expected["token"], 16)
        observed = reader.method(token)
        require(
            {key: observed[key] for key in expected} == expected,
            "a selected managed construction method differs",
        )
        require(
            observed["cil"] and observed["managed"] and not observed["native"],
            "a native body must not be treated as CIL",
        )
        row = reader.image.net.mdtables.MethodDef.rows[(token & 0xFFFFFF) - 1]
        bodies[token] = managed.CilMethodBody(
            managed.CilMethodBodyReaderBytes(reader.image.get_data(row.Rva, 1 << 20))
        )
        methods.append(observed)
    rules = managed_rules(reader, bodies)
    boundaries = []
    for value in knowledge["managed"]["native_tokens"]:
        observed = reader.method(int(value, 16))
        boundary = observed["boundary"]
        require(
            boundary["kind"] == "native-import-thunk"
            and boundary["module"].lower() == "sldmodu.dll",
            "native construction import changed",
        )
        require(
            boundary["symbol"] in exports["sldmodu.dll"],
            "native symbol is absent from the complete export table",
        )
        boundary["target_address"] = hex(exports["sldmodu.dll"][boundary["symbol"]])
        boundary["target_module_sha256"] = images["sldmodu.dll"].sha256
        boundaries.append(observed)
    functions = []
    for expected in knowledge["functions"]:
        name = expected["module"]
        observed = native.pin_function(
            images[name], expected["entry"], *groups[name], expected["leaf_bytes"]
        )
        require(
            observed["total_bytes"] == expected["expected_bytes"]
            and observed["fragment_count"] == expected["expected_fragment_count"]
            and observed["ordered_fragment_sha256"] == expected["expected_sha256"],
            "a complete native construction function differs",
        )
        functions.append({"key": expected["key"], "module": name, **observed})
    calls = [
        {
            "key": selected["key"],
            "module": selected["module"],
            **native.pin_call(images[selected["module"]], selected),
        }
        for selected in knowledge["calls"]
    ]
    for selected in knowledge["virtual_slots"]:
        image = images[selected["module"]]
        address = int(selected["vtable"], 16) + selected["slot_bytes"]
        target = unpack_from("<Q", image.data, image.offset(address - image.base))[0]
        require(
            hex(target) == selected["target"],
            "the actual native lifecycle virtual edge differs",
        )
    result = {
        "schema": "kit.sw2026.cylinder-selected-end-pin.v1",
        "source_pin_passed": True,
        "task_id": knowledge["task_id"],
        "document_version": 19000,
        "tool_sha256": digest(Path(__file__).read_bytes()),
        "knowledge_sha256": digest(raw),
        "dependencies": knowledge["dependencies"],
        "modules": identities,
        "managed_identity": {"mvid": module["mvid"], "cli_flags": module["cli_flags"]},
        "parser_versions": versions,
        "managed_methods": methods,
        "native_boundaries": boundaries,
        "native_functions": functions,
        "native_calls": calls,
        "virtual_slots": knowledge["virtual_slots"],
        "macro_data_map": macro_map(images, knowledge["macro_map"]),
        "derived_managed_rules": rules,
        "recorded_source_rules": knowledge["rules"],
        "prior_frozen_wire": knowledge["prior_frozen_wire"],
        "limits": {
            "native_processes_started": 0,
            "generated_native_files": 0,
            "heldout_inputs_read": 0,
            "hopper_documents_opened": 0,
            "vendor_code_or_bodies_emitted": False,
            "public_enum_translation_qualified": False,
            "native_selected_end_acceptance": False,
        },
    }
    encoded = (
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(
        json.dumps(
            {
                "source_pin_passed": True,
                "sha256": digest(encoded),
                "managed_methods": len(methods),
                "native_functions": len(functions),
                "native_calls": len(calls),
                "native_boundaries": len(boundaries),
                "generated_native_files": 0,
                "native_processes_started": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
