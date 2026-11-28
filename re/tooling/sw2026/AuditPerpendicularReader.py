import argparse
from hashlib import sha256
import json
from math import isclose
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from SdkMatesProcess import load_sdk, worker


def require(value, message):
    if not value:
        raise ValueError(message)


def close_values(actual, expected):
    return len(actual) == len(expected) and all(isclose(first, second, rel_tol=1e-10, abs_tol=1e-12)
                                               for first, second in zip(actual, expected, strict=True))


def numeric_graph(path, sdk):
    archive = sdk["SldprtArchive"].from_bytes(path.read_bytes())
    link = sdk["ReadNativeLink"](archive, 0)
    graph = sdk["ReadMatesMut"](archive.require("Contents/Config-0-MatesList"), link.ResolvedValue)
    mate = graph.RootsValue[0]
    model = sdk["FindModelRoot"](link.ResolvedValue.MapValue)
    rows = []
    parent_epoch = link.ConfigValue.HeaderValue.FieldsValue["f40"]
    for order, (selected_row, resolved_row) in enumerate(zip(mate.FieldsValue["f3c8"], mate.FieldsValue["f410"], strict=True)):
        selected, resolved = selected_row["o"], resolved_row["o"]
        detached_plane, real_plane = selected.FieldsValue["f58"], resolved.FieldsValue["f58"]
        unit, component = detached_plane.FieldsValue["f58"], real_plane.FieldsValue["f58"]
        branch = component.FieldsValue["f20"].FieldsValue["f08"].FieldsValue["f08"][0]["o"]
        occurrence = branch.FieldsValue["f50"]
        require(unit.FieldsValue["owner"] is component.FieldsValue["owner"] is model,
                "the detached and resolved components do not retain their actual model owner")
        require(occurrence.FieldsValue["f4f8"] is branch, "the real occurrence backlink does not alias its inherited external record")
        require(selected.FieldsValue["f08"] == parent_epoch, "detached wrapper does not retain the actual containing header epoch")
        rows.append({"order": order, "selected_key": selected_row["k"],
                     "resolved_wrapper": {key: resolved.FieldsValue[key] for key in ("f08", "f0c", "f50", "f68", "f70", "f74", "f78", "f7c")},
                     "selected_wrapper": {key: selected.FieldsValue[key] for key in ("f08", "f0c", "f50", "f68", "f70", "f74", "f78", "f7c")},
                     "resolved_datum": dict(real_plane.FieldsValue["ff0"]),
                     "detached_datum": dict(detached_plane.FieldsValue["ff0"]),
                     "principal_kind": real_plane.FieldsValue["f100"], "selected_original_datum_id": detached_plane.FieldsValue["f9c"],
                     "detached_inline_plane_id": detached_plane.FieldsValue["ff8"].FieldsValue["f08"],
                     "occurrence_id": occurrence.FieldsValue["f08"],
                     "occurrence_fixed_word": occurrence.FieldsValue["f408"], "occurrence_solve_word": occurrence.FieldsValue["f400"],
                     "actual_model_owner_alias": True, "actual_occurrence_backlink_alias": True})
    return {"mate_id": mate.FieldsValue["f08"], "parent_update_stamp": parent_epoch, "internal_alignment": mate.FieldsValue["f3b4"],
            "solved_state": mate.FieldsValue["f3b8"], "node_flags": mate.FieldsValue["f0c"],
            "auxiliary_help_count": len(mate.FieldsValue["f448"]), "ordered_owners": rows}


def semantic(document, expected):
    document.assert_valid()
    assembly = document.assembly
    report = document.metadata["solidworks.typed_mates_semantics"]
    require(report["status"] == "admitted" and report["scope"] == "ordinary_perpendicular_single_mate_two_direct_part_occurrences"
            and report["full_selected_mate_graph"] and not report["public_writer_qualified"], "the complete perpendicular graph was not admitted")
    require(assembly is not None and len(assembly.mates) == 1 and len(assembly.mate_entities) == 2
            and len(assembly.instances) == 2 and len(assembly.documents) == 1, "the exact repeated part graph differs")
    mate = assembly.mates[0]
    native = expected["mate"]
    require(mate.name == native["name"] and str(mate.kind) == "perpendicular" and str(mate.alignment) == "unknown"
            and mate.value is None and mate.attributes["native_internal_alignment_code"] == 0
            and mate.attributes["native_solved_state_code"] == 1
            and mate.attributes["typed_archive_owner"]["native_feature_id"] == native["native_feature_id"], "the native mate identity or distinct alignment semantics differ")
    occurrences = {item.id: item for item in assembly.instances}
    for entity, target in zip(assembly.mate_entities, native["ordered_endpoints"], strict=True):
        require(len(entity.instance_path) == 1, "the endpoint is not an actual direct occurrence")
        occurrence = occurrences[entity.instance_path[0]]
        require(occurrence.name == target["occurrence"] and occurrence.attributes["native_feature_id"] == target["occurrence_native_id"]
                and entity.source_entity_id == "sldprt:plane:" + str(target["plane_native_id"])
                and entity.attributes["native_datum_name"] == target["plane"], "the ordered occurrence or selected datum differs from native observation")
        require(close_values(entity.attributes["stored_origin_m"], target["point"])
                and close_values(entity.attributes["stored_normal"], target["normal"]), "the selected plane geometry differs from native observation")
    for actual, target in zip(assembly.instances, expected["occurrences"], strict=True):
        values = target["transform"]
        matrix = [*values[:3], 0, *values[3:6], 0, *values[6:9], 0, *values[9:12], 1]
        require(actual.name == target["name"] and actual.fixed == target["fixed"]
                and actual.configuration_name == target["configuration"] and close_values(actual.attributes["native_transform"], matrix),
                "the actual native occurrence configuration anchor or rigid pose differs")
    child = assembly.documents[0].document
    expected_values = [expected["dimensions_m"][key] for key in ("D1@Sketch1", "D2@Sketch1", "D1@Boss-Extrude1")]
    require(close_values([item.value.value / 1000 for item in child.parameters], expected_values)
            and all(item.attributes["native_role"] == "driving" for item in child.parameters), "the normal child reader did not retain all three actual driving lengths")
    return {"status": report["status"], "scope": report["scope"], "mate_name": mate.name, "kind": str(mate.kind),
            "alignment": str(mate.alignment), "internal_alignment": 0, "native_api_alignment_observed": native["alignment_observed"],
            "mate_count": 1, "entity_count": 2, "instance_count": 2, "child_driver_count": len(child.parameters),
            "ordered_native_endpoints_equal": True, "native_occurrence_poses_equal": True, "actual_child_drivers_equal": True,
            "map_base": report["map_base"], "map_terminal": report["map_terminal"], "writer_qualified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    request = json.load(sys.stdin)
    root = args.root.resolve()
    sdk = load_sdk(root)
    path = Path(request["path"])
    child = Path(request["child_path"])
    require(sha256(child.read_bytes()).hexdigest() == request["child_sha256"], "the disclosed child source digest changed")
    codec = worker(root, request)
    from convert import open_document

    document = open_document(path, include_brep=False, include_tessellation=False)
    result = {"codec": codec, "typed_owners": numeric_graph(path, sdk), "public": semantic(document, request["expected"]),
              "public_json_sha256": sha256(document.to_json(indent=None).encode()).hexdigest(),
              "pid": os.getpid(), "passed": True, "writer_output_count": 0,
              "native_processes_started": 0, "heldout_inputs_read": False}
    require(sha256(child.read_bytes()).hexdigest() == request["child_sha256"], "the disclosed child changed during audit")
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
