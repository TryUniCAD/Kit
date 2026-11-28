from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != TOOLS]

import argparse
from copy import deepcopy
from hashlib import sha256
import json

sys.path.append(str(TOOLS))

from InspectOriginPortable import verify_source

sys.path.append(str(TOOLS))

from OriginPortableGraph import Graph, require
from OriginPortableGeometry import rectangle_geometry
from OriginPortableOwners import drawing_owners, extrusion, plane_names
from OriginPortableSettings import drawing_settings, part_settings
from OriginPortableWire import canonical, make_ledger, neutral_child, normalized_drawing, restore


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def known_boundaries(graph, case):
    result = []
    for label, model_ref, history_group in (("child", case["typed_child"]["root"], case["typed_child_history"]),
                                           ("drawing", graph.fields(case["typed_drawing"]["root"])["model"]["$node"], case["typed_drawing_history"])):
        detail = graph.fields(model_ref)["fae0"]
        if detail["f10"] != 1:
            result.append({"field": label + ".model.fae0.f10", "value": detail["f10"], "rule": "MakeDetails admits only independently recovered standard 1"})
        if history_group.get("complete"):
            history = graph.fields(history_group["root"])
            for index, value in enumerate(history["states"]):
                codes = graph.fields(value["st"]["f38"])
                for code_index, row in enumerate(codes["states"]):
                    code = row["st"]["f08"]
                    if not 1 <= code <= 0xFFFFFF:
                        result.append({"field": label + ".version_history.states[" + str(index) + "].date_codes[" + str(code_index) + "]", "value": code,
                                       "rule": "fresh HistoryInput requires explicit truthful nonnative originating writer provenance"})
    manager = graph.fields(case["typed_child_manager"]["root"])
    if manager["f18"] is None:
        result.append({"field": "child.configuration_manager.f18", "value": None, "rule": "ManagerInput currently requires a nonempty authored node name"})
    for atom in graph.members("moAtom_c"):
        if atom["fields"].get("f18c") == 1 and atom["fields"].get("f18") is None:
            result.append({"field": "child.body_atom[" + str(atom["identity"]["object_index"]) + "].name", "rule": "actual kernel-managed body name remains outside this source-only observation; the public Solid Bodies folder label is not a body-name proof"})
    return result


def plain(value, graph=None):
    if isinstance(value, dict):
        if "$cstring" in value:
            return value["$cstring"]
        if "$node" in value:
            require(graph is not None, "style comparison cannot flatten an unresolved node")
            return plain(graph.fields(value), graph)
        return {key: plain(item, graph) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item, graph) for item in value]
    return value


def first_difference(actual, expected, path):
    if isinstance(actual, dict) and isinstance(expected, dict):
        if actual.keys() != expected.keys():
            return path + ": field membership differs"
        return next((value for key in actual if (value := first_difference(actual[key], expected[key], path + "." + key)) is not None), None)
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return path + ": array length differs"
        return next((value for index, (a, b) in enumerate(zip(actual, expected, strict=True)) if (value := first_difference(a, b, path + "[" + str(index) + "]")) is not None), None)
    return None if actual == expected else path + ": source value is outside the constructor's complete style rule"


def validate_styles(graph, model_ref, settings, make_details, swift_fields):
    expected = make_details(StandardValue=settings["standard"], FontName=settings["font_name"], LineStyleName=settings["line_style_name"],
                            LanguageId=settings["language_id"], PrintWidths=settings["print_widths_m"], ExclusionNames=settings["exclusion_names"],
                            TaskLabels=settings["task_labels"], CutlistExpressions=settings["cutlist_expressions"])
    require(len(swift_fields) == 159 and all(field.KindValue == "Scalar" and field.TypeValue in ("i32", "f64") for field in swift_fields),
            "portable source Swift comparison requires its complete ordinary scalar vocabulary")
    runtime = expected["ff68"]
    expected["ff68"] = {field.NameValue: runtime[field.NameValue] if field.NameValue in runtime else runtime[field.OtherName] for field in swift_fields}
    difference = first_difference(plain(graph.fields(model_ref)["fae0"], graph), plain(expected), "model.fae0")
    require(difference is None, difference or "complete source style projection differs")
    return {"all_actual_serialized_style_fields_equal": True, "swift_wire_scalar_occurrences": len(swift_fields),
            "swift_runtime_fields_not_serialized": sorted(set(runtime) - {field.OtherName or field.NameValue for field in swift_fields}),
            "swift_distinct_wire_occurrences": [{"wire_field": field.NameValue, "runtime_field": field.OtherName} for field in swift_fields if field.OtherName],
            "raw_source_fields_changed": False}


def project(case, make_details, binding, swift_fields):
    require(case["intake_complete"] is True and case["public_child_strict"].get("wire_encoding_complete") is True,
            "private portable projection requires complete typed source intake and a real public child document")
    groups = [case[name] for name in ("typed_child", "typed_child_manager", "typed_child_definition", "typed_child_history", "typed_drawing", "typed_drawing_history")]
    graph = Graph(groups)
    result = {"case": case["case"], "role": case["role"], "request_complete": False, "constructor_admitted": False,
              "source_semantic_admission": False, "public_drawing_strict_preserved": case["public_drawing_strict"],
              "known_constructor_boundaries": known_boundaries(graph, case), "unmapped": [], "request": None}
    phase = "actual child geometry and complete relation ownership"
    try:
        geometry = rectangle_geometry(graph, case["typed_child"])
        result["geometry_observed"] = geometry
        for driver in geometry["drivers"]:
            if not driver["constructor_text_representable"]:
                result["known_constructor_boundaries"].append({
                    "field": "child.display[" + str(driver["display"]["object_index"]) + "].f6a0.f38",
                    "owner": driver["display"], "value_xyz_m": driver["text_xyz_m"],
                    "rule": "frozen RectDimInput accepts two planar coordinates and MakeRectDisplay writes z=0; the actual source text point is retained without projection"})
        phase = "actual ordinary blind termination and driving depth"
        boss = extrusion(graph, case["typed_child"], geometry)
        phase = "actual profile support ownership"
        names, selected_plane = plane_names(graph, case, geometry)
        phase = "actual drawing child profile and file configuration aliases"
        owners = drawing_owners(graph, case, geometry, binding)
        model_name = graph.name(case["typed_child"]["root"])
        require(model_name == owners["child_file"]["model_name"], "portable source actual model and self-file names differ")
        result["file_identity_domains"] = {"resolved_child": owners["resolved_child"], "header_self_file": owners["child_file"],
                                          "modeled_name": model_name, "path_equality_is_resolution_gate": False}
        if not owners["resolved_child"]["independent_header_self_path_equal"]:
            result["known_constructor_boundaries"].append({
                "field": "child.Header2.self_file.path", "source_value": owners["child_file"]["path"],
                "resolved_child_path": owners["resolved_child"]["path"],
                "rule": "MakeSelfFile emits the single output path from SelfFileInput; the separate source Header2 self record is retained and is not an alias-resolution gate"})
        source_child = case["public_child_strict"]["document_wire"]
        phase = "actual neutral source domains and implicit normal ownership"
        child, domain_projection = neutral_child(case, geometry, boss, selected_plane, model_name)
        phase = "independent drawing placement and prism projection"
        drawing = normalized_drawing(owners, geometry, boss)
        result.update(geometry_complete=True, geometry=geometry, boss=boss, origins=owners,
                      public_child_sketch_counts={"entities": len(source_child["sketches"]["$tuple"][0]["entities"]["$tuple"]),
                                                  "relations": len(source_child["sketches"]["$tuple"][0]["constraints"]["$tuple"]),
                                                  "typed_line_dimensions": source_child["sketches"]["$tuple"][0]["attributes"].get("typed_line_dimensions") is True},
                      source_actual_driving_values_m=[driver["length_m"] for driver in geometry["drivers"]] + [boss["depth_m"]])
        child_ledger = make_ledger(source_child, child)
        drawing_ledger = make_ledger(owners["drawing_wire"], drawing)
        restored_child, restored_drawing = restore(child, child_ledger), restore(drawing, drawing_ledger)
        require(restored_child == source_child and restored_drawing == owners["drawing_wire"], "private source normalization is not reversible")
        result["normalization"] = {"child_ledger": child_ledger, "drawing_ledger": drawing_ledger,
                                   "source_child_wire_sha256": sha256(canonical(source_child)).hexdigest(),
                                   "restored_child_wire_sha256": sha256(canonical(restored_child)).hexdigest(),
                                   "source_drawing_wire_sha256": sha256(canonical(owners["drawing_wire"])).hexdigest(),
                                   "restored_drawing_wire_sha256": sha256(canonical(restored_drawing)).hexdigest(),
                                   "inverse_equal": True, "inverse_scope": "complete public neutral document wires; actual typed presentation and unprojected state remain separately hash-bound in the intake",
                                   "constructor_only_anchor_projection": {"kind": geometry["kind"], "binary_relations_preserved": geometry["binary_roles"],
                                       "construction_diagonals_preserved": geometry["visible_line_count"] - 4,
                                       "retired_rows_classified_volatile": geometry["retired_line_rows"]},
                                   "unused_supports_moved_to_system_plane_names": names,
                                   "modeled_domains": domain_projection,
                                   "system_feature_names_moved_to_explicit_settings": True,
                                   "public_center_fallback_not_used_as_geometry": True,
                                   "native_payloads_replayed_by_constructor": False}
        result["portable_child_document"] = child
        result["portable_drawing_document"] = drawing
        phase = "complete source-owned constructor metadata"
        settings = part_settings(graph, case, geometry, boss, names)
        native = drawing_settings(graph, case, owners)
        phase = "complete source style semantics against independent constructor rules"
        result["constructor_style_comparison"] = {
            "child": validate_styles(graph, case["typed_child"]["root"], settings["styles"], make_details, swift_fields),
            "drawing": validate_styles(graph, owners["model"], native["options"]["styles"], make_details, swift_fields)}
        require(not result["known_constructor_boundaries"], "source has explicit unsupported constructor metadata body-name or spatial text semantics")
        request = {"schema": "kit.sw2026.sdk-origin-drawing-process.v1", "drawing_document": drawing, "native": native,
                   "part": {"document": child, "settings": settings}, "support_names": owners["support_names"],
                   "child_policy": {"kind": geometry["kind"], "width_text_m": list(geometry["drivers"][0]["text_m"]),
                                    "height_text_m": list(geometry["drivers"][1]["text_m"]), "route_centerline": geometry["drivers"][0]["route_centerline"]},
                   "origin_display": {"selection": "actual-child-origin", "population_argument": 0}}
        result.update(request_complete=True, constructor_admitted=True, request=request, request_sha256=sha256(canonical(request)).hexdigest())
    except (KeyError, TypeError, ValueError) as error:
        result["unmapped"].append({"phase": phase, "exception": type(error).__name__, "diagnostic": str(error)})
    return result


def main():
    parser = argparse.ArgumentParser(description="Normalize only disclosed exact origin-linked drawings without relaxing the public reader or constructor")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("intake", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--intake-sha256", required=True)
    parser.add_argument("--tool-manifest", type=Path, required=True)
    parser.add_argument("--tool-manifest-sha256", required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "portable normalization output must be unused")
    require(args.tool_manifest.resolve().parent / "Tools" == TOOLS and not args.tool_manifest.is_symlink(),
            "portable normalization must execute beside its frozen tool manifest")
    require(digest(args.intake) == args.intake_sha256 and digest(args.tool_manifest) == args.tool_manifest_sha256, "portable normalization input or tool custody differs")
    tool_manifest = json.loads(args.tool_manifest.read_bytes())
    require(tool_manifest["schema"] == "kit.sw2026.origin-portable-normalization-tools.v1"
            and tool_manifest["source_manifest_sha256"] == args.manifest_sha256 and tool_manifest["intake_sha256"] == args.intake_sha256,
            "portable normalization method differs from its exact frozen disclosed intake")
    require({row["path"] for row in tool_manifest["files"]} == {"InspectOriginPortable.py", "NormalizeOriginPortable.py", "OriginPortableGraph.py", "OriginPortableGeometry.py", "OriginPortableOwners.py", "OriginPortableSettings.py", "OriginPortableWire.py"},
            "portable normalization tool membership differs")
    for row in tool_manifest["files"]:
        path = TOOLS / row["path"]
        require(path.is_file() and path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], "portable normalization tool changed")
    manifest = verify_source(args.candidate, args.manifest_sha256)
    intake = json.loads(args.intake.read_bytes())
    require(intake["source_manifest_sha256"] == args.manifest_sha256 and intake["data_collected"] is True and intake["source_immutable"] is True,
            "portable normalization requires the complete immutable exact source observation")
    require(intake.get("actual_node_references_retained_for_entire_case") is True,
            "portable normalization requires observation identities backed by retained actual node owners")
    require(len(intake["cases"]) == 8 and sorted(row["role"] for row in intake["cases"]) == ["disclosed"] * 4 + ["generated-replay06"] * 4,
            "portable normalization scope differs from the eight disclosed pairs")
    sys.path[:0] = [str(args.candidate / "CodeRoot/src"), str(args.candidate / "CodeRoot")]
    from convert.adapters.solidworks.Archive.Construction.Styles.MakeDetails import MakeDetails
    from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.CommonFields import KCommonFields
    bindings = tool_manifest["source_pair_bindings"]
    require(type(bindings) is list and len(bindings) == 8 and len({row["case"] for row in bindings}) == 8,
            "portable normalization pair-origin binding membership differs")
    by_case = {row["case"]: row for row in bindings}
    require(set(by_case) == {row["case"] for row in intake["cases"]}, "portable normalization pair-origin binding scope differs")
    results = [project(case, MakeDetails, by_case[case["case"]], KCommonFields["moSwiftGtsOptions_c"]) for case in intake["cases"]]
    args.output.mkdir(parents=True, exist_ok=False)
    for index, row in enumerate(results):
        if row["request_complete"]:
            path = args.output / (str(index) + ".Request.json")
            with path.open("x", encoding="utf-8") as stream:
                json.dump(row["request"], stream, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
            row["request_file"] = {"path": path.name, "sha256": digest(path), "bytes": path.stat().st_size}
    report = {"schema": "kit.sw2026.origin-portable-normalization.v1", "intake_sha256": args.intake_sha256, "source_manifest_sha256": args.manifest_sha256,
              "source_file_count": manifest["file_count"], "tool_manifest_sha256": args.tool_manifest_sha256, "cases": results,
              "data_collected": True, "request_count": sum(row["request_complete"] for row in results),
              "reversible_source_normalization_count": sum(row.get("normalization", {}).get("inverse_equal") is True for row in results),
              "source_semantic_admission": False, "public_strict_drawing_reader_changed": False, "writer_changed": False,
              "native_acceptance": False, "heldout_acceptance": False, "hidden_inputs_read": 0,
              "private_requests_require_independent_guarded_reconstruction": True}
    with (args.output / "Result.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in ("data_collected", "request_count", "reversible_source_normalization_count", "source_semantic_admission")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
