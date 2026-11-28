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


def load_module(root, relative, expected):
    path = root / relative
    require(digest(path.read_bytes()) == expected, "shared evidence dependency differs")
    spec = importlib.util.spec_from_file_location("angled_" + path.stem, path)
    require(spec is not None and spec.loader is not None, "evidence helper is absent")
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
    raise ValueError("selected instruction is not an integer argument")


def call_sites(body, token):
    return [
        index
        for index, item in enumerate(body.instructions)
        if item.opcode.name in ("call", "callvirt", "newobj")
        and item.operand.value == token
    ]


def allocation(body):
    sites = call_sites(body, 0x06004270)
    require(len(sites) == 1, "one concrete constructor allocation is required")
    index = sites[0]
    require(
        body.instructions[index - 1].opcode.name == "conv.i8",
        "allocation width differs",
    )
    return integer(body.instructions[index - 2])


def mode_store(body):
    sites = [
        index
        for index, item in enumerate(body.instructions)
        if item.opcode.name == "stind.i4"
    ]
    require(len(sites) == 1, "one native mode assignment is required")
    index = sites[0]
    require(
        [item.opcode.name for item in body.instructions[index - 3 : index - 1]]
        == ["conv.i8", "add"],
        "native mode destination is not a pointer plus offset",
    )
    return {
        "owner_offset": hex(integer(body.instructions[index - 4])),
        "mode": integer(body.instructions[index - 1]),
    }


def has_integer(body, value):
    return any(
        integer(item) == value
        for item in body.instructions
        if item.opcode.name.startswith("ldc.i4")
    )


def managed_rules(bodies):
    sizes = {
        "constrained_angle_plane": allocation(bodies[0x06004F2B]),
        "compatibility_angle_plane": allocation(bodies[0x06004D05]),
        "selected_angle_geometry": allocation(bodies[0x06004C73]),
        "actual_plane_feature": allocation(bodies[0x06004C03]),
    }
    require(
        sizes
        == {
            "constrained_angle_plane": 344,
            "compatibility_angle_plane": 184,
            "selected_angle_geometry": 72,
            "actual_plane_feature": 1792,
        },
        "concrete plane allocation changed",
    )
    modes = {
        "constrained_angle_plane": mode_store(bodies[0x06004F2B]),
        "compatibility_angle_plane": mode_store(bodies[0x06004D05]),
    }
    require(
        modes
        == {
            "constrained_angle_plane": {"owner_offset": "0x5c", "mode": 22},
            "compatibility_angle_plane": {"owner_offset": "0x5c", "mode": 7},
        },
        "plane-data type publication changed",
    )
    feature = bodies[0x06004C03]
    sites = call_sites(feature, 0x06004414)
    require(len(sites) == 1, "the actual feature has no unique plane-data init")
    flag = integer(feature.instructions[sites[0] - 1])
    require(flag == 1 and has_integer(feature, 16), "plane owner or init flag changed")
    require(
        len(call_sites(bodies[0x06004C73], 0x0600441E)) == 1
        and len(call_sites(bodies[0x06004F2B], 0x06004483)) == 1
        and len(call_sites(bodies[0x06004D05], 0x06004417)) == 1,
        "concrete native constructor edge changed",
    )
    require(
        has_integer(bodies[0x06004E15], 3)
        and len(call_sites(bodies[0x06004E15], 0x06004C44)) == 1,
        "three ordered virtual geometry creations changed",
    )
    require(
        len(call_sites(bodies[0x06004F33], 0x06004CFD)) == 1
        and len(call_sites(bodies[0x06004F33], 0x06004CFF)) == 1
        and len(call_sites(bodies[0x06004DA7], 0x06004446)) == 1
        and len(call_sites(bodies[0x06004DA8], 0x0600440B)) == 2
        and has_integer(bodies[0x06004DA8], 0x868),
        "reference order or actual angular display owner changed",
    )
    require(
        has_integer(bodies[0x06004DE0], 4150)
        and len(call_sites(bodies[0x06004F32], 0x06004DE2)) == 1,
        "old/API construction guard changed",
    )
    return {
        "allocation_bytes": sizes,
        "published_modes": modes,
        "plane_owner_offset": "0x10",
        "feature_initialization_flag": flag,
        "ordered_geometry_slot_count": 3,
        "compatibility_preserves_both_reference_indexes": True,
        "managed_angle_readback_follows_actual_display": True,
        "managed_display_value_virtual_offset": "0x868",
        "old_creation_version_threshold": 4150,
    }


def native_slots(image, selected):
    for row in selected:
        address = int(row["vtable"], 16) + row["slot_bytes"]
        actual = unpack_from("<Q", image.data, image.offset(address - image.base))[0]
        require(hex(actual) == row["target"], "selected native virtual target differs")
    return selected


def runtime_publications(image, selected):
    results = []
    for row in selected:
        address = int(row["getter"], 16)
        raw = image.data[
            image.offset(address - image.base) : image.offset(address - image.base) + 8
        ]
        require(
            raw[:3] == b"\x48\x8d\x05" and raw[7] == 0xC3,
            "runtime publication getter differs",
        )
        target = address + 7 + unpack_from("<i", raw, 3)[0]
        require(
            hex(target) == row["descriptor"], "published archive descriptor differs"
        )
        results.append(row)
    return results


def constants(image, selected):
    rows = []
    for expected in selected:
        address = int(expected["address"], 16)
        value = unpack_from("<d", image.data, image.offset(address - image.base))[0]
        require(value == expected["value"], "native angular constant differs")
        rows.append({"address": expected["address"], "value": value})
    return rows


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "the output must be new")
    raw = args.knowledge.read_bytes()
    knowledge = json.loads(raw)
    require(
        knowledge["schema"] == "kit.sw2026.cylinder-angled-planes.v1",
        "knowledge schema differs",
    )
    require(
        knowledge["document_version"] == 19000,
        "angular plane evidence requires version 19000",
    )
    helpers = {
        relative: load_module(args.root, relative, expected)
        for relative, expected in knowledge["dependencies"].items()
    }
    pe = helpers["re/tooling/sw2026/freecad_cylinder/NativeNamePe.py"].NativeNamePe
    native = helpers["re/tooling/sw2026/freecad_cylinder/PinCylinderDirectionWire.py"]
    managed = helpers["re/tooling/sw2026/ManagedConstructionIndex.py"]
    versions = {
        name: importlib.metadata.version(name) for name in managed.PARSER_VERSIONS
    }
    require(versions == managed.PARSER_VERSIONS, "managed parser versions differ")
    images = {}
    identities = []
    for name, expected in knowledge["modules"].items():
        image = pe((args.inputs / name).read_bytes())
        require(
            image.sha256 == expected["sha256"]
            and len(image.data) == expected["bytes"]
            and hex(image.base) == expected["base"]
            and hex(image.machine) == expected["machine"],
            "pinned angular plane original image differs",
        )
        images[name] = image
        identities.append({"name": name, **expected})
    image = images["sldmodu.dll"]
    names = native.exports(image)
    groups = native.unwind_groups(image)
    reader = managed.ManagedIndex(
        args.inputs / "sldcoreu.dll", images["sldcoreu.dll"].sha256, None, None
    )
    module = reader.receipt([], False)["module"]
    require(
        module["mvid"] == knowledge["managed"]["mvid"]
        and module["cli_flags"] == knowledge["managed"]["cli_flags"],
        "managed identity differs",
    )
    methods, bodies = [], {}
    for expected in knowledge["managed"]["methods"]:
        token = int(expected["token"], 16)
        observed = reader.method(token)
        require(
            {key: observed[key] for key in expected} == expected,
            "selected managed method differs",
        )
        require(
            observed["cil"] and observed["managed"] and not observed["native"],
            "native code must not be decoded as CIL",
        )
        row = reader.image.net.mdtables.MethodDef.rows[(token & 0xFFFFFF) - 1]
        bodies[token] = managed.CilMethodBody(
            managed.CilMethodBodyReaderBytes(reader.image.get_data(row.Rva, 1 << 20))
        )
        methods.append(observed)
    boundaries = []
    for expected in knowledge["managed"]["native_boundaries"]:
        observed = reader.method(int(expected["token"], 16))
        boundary = observed["boundary"]
        require(
            boundary["kind"] == "native-import-thunk"
            and boundary["module"].lower() == "sldmodu.dll",
            "native model import differs",
        )
        boundary["target_address"] = hex(names[boundary["symbol"]])
        require(
            boundary["target_address"] == expected["target_address"],
            "native constructor target differs",
        )
        boundaries.append(observed)
    functions = []
    for expected in knowledge["functions"]:
        observed = native.pin_function(
            image, expected["entry"], *groups, expected["leaf_bytes"]
        )
        require(
            observed["total_bytes"] == expected["expected_bytes"]
            and observed["fragment_count"] == expected["expected_fragments"]
            and observed["ordered_fragment_sha256"] == expected["expected_sha256"],
            "complete native function differs",
        )
        functions.append({"key": expected["key"], **observed})
    classes = [
        native.pin_class(image, selected, names) for selected in knowledge["classes"]
    ]
    calls = [
        {"key": selected["key"], **native.pin_call(image, selected)}
        for selected in knowledge["calls"]
    ]
    result = {
        "schema": "kit.sw2026.cylinder-angled-planes-pin.v1",
        "task_id": knowledge["task_id"],
        "source_pin_passed": True,
        "tool_sha256": digest(Path(__file__).read_bytes()),
        "knowledge_sha256": digest(raw),
        "dependencies": knowledge["dependencies"],
        "document_version": 19000,
        "modules": identities,
        "managed_identity": {"mvid": module["mvid"], "cli_flags": module["cli_flags"]},
        "parser_versions": versions,
        "managed_methods": methods,
        "native_boundaries": boundaries,
        "native_functions": functions,
        "runtime_classes": classes,
        "runtime_publications": runtime_publications(
            image, knowledge["runtime_publications"]
        ),
        "virtual_slots": native_slots(image, knowledge["virtual_slots"]),
        "native_calls": calls,
        "native_constants": constants(image, knowledge["constants"]),
        "derived_managed_rules": managed_rules(bodies),
        "recorded_field_rules": knowledge["field_rules"],
        "prior_packets": knowledge["prior_packets"],
        "limits": {
            "native_processes_started": 0,
            "generated_native_files": 0,
            "heldout_inputs_read": 0,
            "hopper_documents_opened": 0,
            "vendor_code_or_bodies_emitted": False,
            "angular_plane_source_corpus_qualified": False,
            "angular_plane_writer_qualified": False,
            "native_oblique_cylinder_acceptance": False,
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
                "runtime_classes": len(classes),
                "native_processes_started": 0,
                "generated_native_files": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
