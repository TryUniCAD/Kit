from __future__ import annotations

import argparse
import json
import math
import re
import time
from itertools import islice
from pathlib import Path
from shutil import copyfile

from AuthorCurves import Recorder, digest, require, write_json


SCHEMA = "kit.sw2026.generated-coincident-mate-proof.v1"
SOURCE_LOCK_SHA = "8f79ed2aa8559b7186f414330b495ce50c4fa3612f69d421bbd7bc83037ca417"
SOURCE_SPECS_SHA = "642066a5493d58c09e68e5965b315c741c56be75541e53d17f66077a5d0909d8"
CONTROL_NAME = "A17PlaneCoincident"
CONTROL_CHILD = "CohortChild.SLDPRT"
WORK_DIRECTORY = "GeneratedInput"
DIMENSIONS = ("D1@Sketch1", "D2@Sketch1", "D1@Boss-Extrude1")
TOOL_FILES = (
    "AssemblyMateEvidence.py", "AuthorAssemblySources.py", "AuthorCurves.py", "InspectCircleSketch.py",
    "InspectFresh.py", "ObserveAssemblyLoad.py", "OracleIdentity.py", "ProbeAssemblyRebuild.py",
    "Swapp.py", "InspectGeneratedCoincidentMate.py",
)


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def finite(value):
    return type(value) in (float, int) and math.isfinite(value)


def close(value, expected, *, relative=5e-7, absolute=1e-14):
    return finite(value) and math.isclose(value, expected, rel_tol=relative, abs_tol=absolute)


def dot(first, second):
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def plane_residual(first_point, first_normal, second_point, second_normal):
    delta = [second - first for first, second in zip(first_point, second_point, strict=True)]
    return {"normal_dot": dot(first_normal, second_normal), "signed_offset_m": dot(first_normal, delta)}


def validate_case(case):
    parent = case["name"]
    child = case["child"]
    require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", parent) and
            re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*\.SLDPRT", child), "invalid proof filenames")
    require(case["configuration"] == "Default" and case["fixed_occurrence"] == 0, "proof requires a fixed first occurrence and Default configuration")
    names = case["occurrence_names"]
    require(len(names) == 2 and len(set(names)) == 2 and all(isinstance(name, str) and name for name in names), "proof requires two distinct authored occurrence names")
    require(case["mates"] == [{"name": "Coincident1", "kind": "coincident", "planes": [[0, "Top Plane"], [1, "Top Plane"]]}], "proof requires one ordered coincident Top Plane mate")
    placements = case["placements"]
    require(len(placements) == 2, "proof requires two placements")
    for placement in placements:
        translation = placement["translation_m"]
        angle = placement["angle_deg"]
        require(placement["axis"] in ("x", "y", "z") and finite(angle) and len(translation) == 3 and all(map(finite, translation)), "invalid authored placement")
        require(placement["axis"] == "y" or angle == 0, "ordinary aligned Top Plane proof requires Y rotation or identity")
    first, second = (row["translation_m"] for row in placements)
    require(first[1] == second[1] and (first[0], first[2]) != (second[0], second[2]), "mate inputs must start coplanar in distinct positions")
    dimensions = case["dimensions_m"]
    require(set(dimensions) == set(DIMENSIONS) and all(finite(value) and value > 0 for value in dimensions.values()), "proof requires three positive driving prism dimensions")
    require(case["rectangle_position"] in ("centered", "corner"), "unknown rectangle origin convention")
    if "edit_depth_m" in case:
        depth = case["edit_depth_m"]
        require(finite(depth) and depth > 0 and depth != dimensions[DIMENSIONS[2]], "proof requires a changed positive depth")


def checked(path, sha, *, owner, size=None):
    resolved = path.resolve(strict=True)
    require(not path.is_symlink() and resolved.is_file() and resolved.is_relative_to(owner), f"proof input escaped its directory: {path.name}")
    require(valid_sha(sha) and digest(resolved) == sha and (size is None or resolved.stat().st_size == size), f"proof input differs from its manifest: {path.name}")
    return resolved


def pair_paths(directory, case, files):
    names = (case["name"] + ".SLDASM", case["child"])
    require(set(files) == set(names), "native proof requires exactly its named parent and child")
    owner = directory.resolve(strict=True)
    return tuple(checked(directory / name, files[name]["sha256"], owner=owner, size=files[name]["bytes"]) for name in names)


def packet_inputs(packet_path, expected_hash):
    require(packet_path.name == "Trial.json" and valid_sha(expected_hash) and digest(packet_path) == expected_hash, "proof packet digest differs")
    root = packet_path.parent
    packet = json.loads(packet_path.read_bytes())
    require(packet["schema"] == SCHEMA and packet["source_lock_sha256"] == SOURCE_LOCK_SHA and
            packet["source_specs_sha256"] == SOURCE_SPECS_SHA and valid_sha(packet["oracle_sha256"]), "proof provenance differs")
    require(packet["native_acceptance"] is False and packet["heldout_inputs_tested"] == 0, "first mate trial must remain disclosed")
    require(set(packet["tool_hashes"]) == set(TOOL_FILES), "proof tool inventory differs")
    tools = (root / "Tools").resolve(strict=True)
    require(Path(__file__).resolve().parent == tools and tools.is_relative_to(root), "run the frozen guest tool copy")
    for name, sha in packet["tool_hashes"].items():
        checked(tools / name, sha, owner=tools)
    generated, control = (packet[label] for label in ("generated", "control"))
    for entry in (generated, control):
        validate_case(entry["case"])
    require(generated["case"]["rectangle_position"] == "corner" and "edit_depth_m" in generated["case"], "generated proof requires an authored corner prism and depth edit")
    require(control["case"]["name"] == CONTROL_NAME and control["case"]["child"] == CONTROL_CHILD and
            "edit_depth_m" not in control["case"], "proof control must be the disclosed immutable A17 pair")
    relative = Path(control["relative_directory"])
    require(not relative.anchor and ".." not in relative.parts and relative.parts[-2:] == (CONTROL_NAME, "author"), "proof control directory is not disclosed A17")
    control_dir = (root.parent / relative).resolve(strict=True)
    frozen = (root / "FrozenGenerated").resolve(strict=True)
    require(control_dir.is_relative_to(root.parent) and not control_dir.is_relative_to(root) and frozen.is_relative_to(root), "proof input directories overlap or escape custody")
    for name, key in (("Prediction.json", "prediction_sha256"), ("AuthoredPrediction.json", "authored_prediction_sha256"),
                      ("GeneratorReport.json", "generator_report_sha256")):
        checked(root / name, generated[key], owner=root)
    require(json.loads((root / "Prediction.json").read_bytes()) == generated["case"], "generated case differs from the frozen observation prediction")
    return packet, pair_paths(control_dir, control["case"], control["files"]), pair_paths(frozen, generated["case"], generated["files"])


def properties(dimensions, position):
    width, height, depth = (dimensions[key] for key in DIMENSIONS)
    volume = width * height * depth
    center = [width / 2, height / 2, depth / 2] if position == "corner" else [0.0, 0.0, depth / 2]
    return {"volume": volume, "area": 2 * (width * height + width * depth + height * depth), "com": center}


def exact_file(actual, expected):
    path = Path(str(actual))
    return path.is_file() and path.samefile(expected)


def configuration(author, document):
    manager = author.get(document, "ConfigurationManager")
    active = author.get(manager, "ActiveConfiguration")
    return {"names": list(author.get(document, "GetConfigurationNames") or ()), "active": str(author.get(active, "Name"))}


def scene_occurrences(author, assembly, child_path, case, transforms, scene):
    from AuthorAssemblySources import transform_matches

    names = case["occurrence_names"]
    components = author.get(assembly, "GetComponents", True) or ()
    scene["component_counts"] = [int(author.get(assembly, "GetComponentCount", flag)) for flag in (True, False)]
    require(scene["component_counts"] == [2, 2] and len(components) == 2, "the assembly did not resolve two top-level components")
    by_name = {}
    for raw in components:
        component = author.typed(raw, "Component2")
        name = str(author.get(component, "Name2"))
        require(name in names and name not in by_name, "native occurrence name or uniqueness differs")
        child = author.get(component, "GetModelDoc2")
        require(child is not None, "native occurrence does not resolve a component document")
        occurrence_path = str(author.get(component, "GetPathName"))
        document_path = str(author.get(child, "GetPathName"))
        path_matches = all(exact_file(path, child_path) for path in (occurrence_path, document_path))
        values = author.typed(author.get(component, "Transform2"), "MathTransform")
        matrix = [float(value) for value in author.get(values, "ArrayData")]
        part = author.typed(child, "PartDoc")
        row = {
            "name": name, "configuration": str(author.get(component, "ReferencedConfiguration")),
            "fixed": bool(author.get(component, "IsFixed")), "suppressed": bool(author.get(component, "IsSuppressed")),
            "visible_child_bodies": len(author.get(part, "GetBodies2", 0, True) or ()),
            "child_path_matches": path_matches, "child_path": document_path,
            "transform": matrix, "transform_matches": transform_matches(matrix, transforms[names.index(name)]),
        }
        by_name[name] = row, child
        scene.setdefault("occurrences", []).append(row)
    rows = scene["occurrences"] = [by_name[name][0] for name in names]
    scene["body_count"] = sum(row["visible_child_bodies"] for row in rows)
    scene["occurrences_match"] = all(
        row["child_path_matches"] and row["transform_matches"] and row["configuration"] == case["configuration"] and
        row["fixed"] == (index == case["fixed_occurrence"]) and not row["suppressed"] and row["visible_child_bodies"] == 1
        for index, row in enumerate(rows)
    )
    require(all(row["child_path_matches"] for row in rows), "native occurrence resolves outside the exact expected child")
    return by_name[names[0]][1]


def reference_comparison(author, entity, feature):
    import Swapp

    result = {}
    try:
        reference = Swapp.cv(entity, "Reference")
        result["returned_reference"] = reference is not None
        if reference is not None:
            result["feature_equality"] = int(Swapp.invoke(author.app, "IsSame", reference, feature))
            if result["feature_equality"] != 1:
                plane = Swapp.cv(feature, "GetSpecificFeature2")
                if plane is not None:
                    result["plane_equality"] = int(Swapp.invoke(author.app, "IsSame", reference, plane))
    except Exception as error:
        result["comparison_error"] = repr(error)
    return result


def observe_mate(author, parent, child_path, case, scene):
    from AssemblyMateEvidence import DATUM_PLANE_SELECTION_TYPE, mate_features, require_plane

    features = list(islice(mate_features(author, parent), 2))
    scene["mate_count_at_most_two"] = len(features)
    require(len(features) == 1, "native mate group does not contain exactly one mate")
    feature = features[0]
    mate = author.typed(author.get(feature, "GetSpecificFeature2"), "Mate2")
    row = scene["mate"] = {
        "name": str(author.get(feature, "Name")), "feature_type": str(author.get(feature, "GetTypeName2")),
        "suppressed": bool(author.get(feature, "IsSuppressed")), "type": int(author.get(mate, "Type")),
        "alignment": int(author.get(mate, "Alignment")), "entity_count": int(author.get(mate, "GetMateEntityCount")),
        "entities": [],
    }
    require(row["entity_count"] == 2, "native mate does not expose two endpoints")
    request = case["mates"][0]
    for index, (placement, plane) in enumerate(request["planes"]):
        entity = author.typed(author.get(mate, "MateEntity", index), "MateEntity2")
        component = author.typed(author.get(entity, "ReferenceComponent"), "Component2")
        reference_type = int(author.get(entity, "ReferenceType2"))
        values = [float(value) for value in author.get(entity, "EntityParams") or ()]
        endpoint = {"occurrence": str(author.get(component, "Name2")), "reference_type": reference_type,
                    "point": values[:3], "normal": values[3:6]}
        row["entities"].append(endpoint)
        occurrence = scene["occurrences"][placement]
        require(endpoint["occurrence"] == occurrence["name"], "native mate endpoint order or occurrence differs")
        require(reference_type == DATUM_PLANE_SELECTION_TYPE and len(values) == 8 and all(map(finite, values)),
                "native mate endpoint does not describe a datum plane")
        model = author.get(component, "GetModelDoc2")
        endpoint["child_path_matches"] = bool(model is not None and exact_file(author.get(model, "GetPathName"), child_path))
        require(endpoint["child_path_matches"], "native mate endpoint resolves outside the exact child")
        named = author.get(component, "FeatureByName", plane)
        require(named is not None and author.get(named, "GetTypeName2") == "RefPlane", "mate's named child datum is unavailable")
        require_plane(endpoint, occurrence["transform"], plane)
        endpoint["resolved_principal_plane"] = plane
        endpoint["reference_comparison"] = reference_comparison(author, entity, named)
    first, second = row["entities"]
    row["api_plane_residual"] = plane_residual(first["point"], first["normal"], second["point"], second["normal"])
    first, second = (item["transform"] for item in scene["occurrences"])
    row["placement_plane_residual"] = plane_residual(first[9:12], first[3:6], second[9:12], second[3:6])
    row["matches"] = bool(row["name"] == request["name"] and row["feature_type"] == "MateCoincident" and
                          not row["suppressed"] and row["type"] == row["alignment"] == 0 and
                          all(close(check["normal_dot"], 1.0, relative=0.0, absolute=1e-10) and abs(check["signed_offset_m"]) <= 1e-10
                              for check in (row["api_plane_residual"], row["placement_plane_residual"])))


def observe_scene(author, parent, assembly, child_path, entry, dimensions, scene):
    import Swapp
    from AuthorAssemblySources import feature_tree, placement_transform, transform_point
    from ProbeAssemblyRebuild import model_state

    case = entry["case"]
    scene["parent_state"] = model_state(author, parent)
    transforms = [placement_transform(value) for value in case["placements"]]
    child = scene_occurrences(author, assembly, child_path, case, transforms, scene)
    scene["child_state"] = model_state(author, child)
    scene["child_stamp"] = int(author.get(child, "GetUpdateStamp"))
    observe_mate(author, parent, child_path, case, scene)
    scene["parent_tree"] = feature_tree(author, parent)
    scene["child_tree"] = feature_tree(author, child)
    projected = [[row[field] for field in ("name", "type", "parent")] for row in scene["parent_tree"]]
    scene["tree_matches"] = projected == entry["expected_tree"]
    scene["child_planes_match"] = {row["name"] for row in scene["child_tree"] if row["type"] == "RefPlane"} == {"Front Plane", "Top Plane", "Right Plane"}
    scene["child_design_features_match"] = {"Origin", "Sketch1", "Boss-Extrude1"} <= {row["name"] for row in scene["child_tree"]}
    scene["configurations"] = [configuration(author, doc) for doc in (parent, child)]
    config = case["configuration"]
    scene["configurations_match"] = scene["configurations"] == [{"names": [config], "active": config}] * 2
    scene["child_dimensions_m"] = Swapp.parameters(child, DIMENSIONS)
    scene["dimensions_match"] = all(close(scene["child_dimensions_m"].get(key), dimensions[key], relative=0.0, absolute=1e-12) for key in DIMENSIONS)
    expected = properties(dimensions, case["rectangle_position"])
    centers = [transform_point(matrix, expected["com"]) for matrix in transforms]
    assembly_expected = {"volume": 2 * expected["volume"], "area": 2 * expected["area"],
                         "com": [math.fsum(center[axis] for center in centers) / 2 for axis in range(3)]}
    scene["expected_geometry"] = {"child": expected, "assembly": assembly_expected}
    scene["mass_properties"] = {"child": Swapp.mass(child), "assembly": Swapp.mass(parent)}
    scene["geometry_matches"] = all(
        isinstance(actual, dict) and "error" not in actual and finite(actual.get("mass")) and actual["mass"] > 0 and
        all(close(actual.get(key), target[key]) for key in ("volume", "area")) and
        len(actual.get("com", ())) == 3 and all(close(value, wanted, absolute=1e-12) for value, wanted in zip(actual["com"], target["com"], strict=True))
        for name, target in scene["expected_geometry"].items() for actual in (scene["mass_properties"][name],)
    )
    scene["passed"] = bool(scene["mate"]["matches"] and scene["body_count"] == 2 and
                           scene["parent_state"]["whats_wrong"] == scene["child_state"]["whats_wrong"] == 0 and
                           all(scene[key] for key in ("occurrences_match", "tree_matches", "child_planes_match", "child_design_features_match",
                                                     "configurations_match", "dimensions_match", "geometry_matches")))
    return child


def save_owned(author, document, path, result):
    import Swapp

    require(exact_file(author.get(document, "GetPathName"), path), "save target is not its exact owned working-copy file")
    result["before_sha256"] = digest(path)
    result["before_stamp"] = int(author.get(document, "GetUpdateStamp"))
    author.get(document, "SetSaveFlag")
    require(bool(author.get(document, "GetSaveFlag")), "owned working copy did not become dirty")
    errors, warnings = Swapp.byref_long(), Swapp.byref_long()
    saved = author.rec.call("save current owned working copy", Swapp.invoke, document, "Save3", Swapp.SAVE_SILENT, errors, warnings)
    result["status"] = [bool(saved), int(errors.value), int(warnings.value)]
    result["after_sha256"] = digest(path) if path.is_file() else None
    result["after_stamp"] = int(author.get(document, "GetUpdateStamp"))
    result["bytes"] = path.stat().st_size if path.is_file() else 0
    return result["status"] == [True, 0, 0] and result["bytes"] > 0


def measure_phase(packet, entry, files, result, output, *, mode, saved=None):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    parent_path, child_path = files
    initial_hashes = {path.name: digest(path) for path in files}
    result.update(mode=mode, input_sha256=initial_hashes, passed=False)
    recorder = Recorder(output / (result["label"] + "Calls.json"), {"lane": result["label"], "mode": mode})
    controller = parent = None
    dimensions = entry["case"]["dimensions_m"]
    if mode == "reopen":
        dimensions = dimensions | {DIMENSIONS[2]: entry["case"]["edit_depth_m"]}
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = recorder.call("verify pinned SOLIDWORKS executable", application_identity, controller.app)
            result["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == packet["oracle_sha256"] and controller.revision == "34.5.2", "oracle build differs")
            author = CurveAuthor(controller.app, recorder, Swapp)
            parent, errors, warnings = recorder.call("open native assembly at its same path", controller.open, parent_path, read_only=mode != "edit")
            result.update(opened=parent is not None, open_errors=errors, open_warnings=warnings)
            require(parent is not None and exact_file(author.get(parent, "GetPathName"), parent_path), "oracle did not open the exact parent input")
            assembly = author.typed(parent, "AssemblyDoc")

            def capture(label, expected):
                scene = result[label] = {"passed": False}
                try:
                    return recorder.call(f"measure {label} mate, occurrences and bodies", observe_scene,
                                         author, parent, assembly, child_path, entry, expected, scene)
                except Exception as error:
                    scene["exception"] = repr(error)
                    return None

            capture("initial", dimensions)
            result["forced_rebuild"] = bool(recorder.call("force parent rebuild", author.get, parent, "ForceRebuild3", False))
            child = capture("rebuilt", dimensions)
            base_passed = bool(errors == warnings == 0 and result["forced_rebuild"] and
                               result["initial"]["passed"] and result["rebuilt"]["passed"])
            if mode == "control":
                result["control_child_stamp_matches"] = result["initial"].get("child_stamp") == entry["expected_child_stamp"]
                base_passed = base_passed and result["control_child_stamp_matches"]
            result["base_passed"] = base_passed
            if mode == "reopen":
                result["saved_input_matches"] = bool(initial_hashes == saved["files"] and
                                                     result["initial"].get("child_stamp") == saved["child"]["after_stamp"])
            if mode == "edit" and base_passed:
                edit_depth = entry["case"]["edit_depth_m"]
                parameter = author.get(child, "Parameter", DIMENSIONS[2])
                require(parameter is not None, "the driving child depth is unavailable")
                author.set(parameter, "SystemValue", edit_depth)
                result["child_edit_rebuilt"] = bool(author.get(child, "ForceRebuild3", False))
                result["application_edit_rebuilt"] = bool(author.get(parent, "ForceRebuild3", False))
                edited_child = capture("edited", dimensions | {DIMENSIONS[2]: edit_depth})
                if result["child_edit_rebuilt"] and result["application_edit_rebuilt"] and result["edited"]["passed"]:
                    save = result["save"] = {"child": {}, "parent": {}, "passed": False}
                    child_saved = save_owned(author, edited_child, child_path, save["child"])
                    require(child_saved and save["child"]["before_stamp"] == save["child"]["after_stamp"], "child save failed, warned or advanced its update stamp")
                    parent_saved = save_owned(author, parent, parent_path, save["parent"])
                    save["files"] = {path.name: digest(path) for path in files if path.is_file()}
                    save["child_unchanged_by_parent"] = (save["files"].get(child_path.name) == save["child"]["after_sha256"] and
                                                         int(author.get(edited_child, "GetUpdateStamp")) == save["child"]["after_stamp"])
                    save["passed"] = bool(parent_saved and save["child_unchanged_by_parent"] and
                                          len(save["files"]) == 2 and all(save["files"][name] != old for name, old in initial_hashes.items()))
            result["passed"] = bool(base_passed and (mode != "edit" or result.get("save", {}).get("passed")) and
                                    (mode != "reopen" or result["saved_input_matches"]))
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if controller is not None:
                if parent is not None:
                    controller.close_doc(parent)
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = monitor.log
    result["progress_windows"] = monitor.progress
    result["read_only_files_unchanged"] = mode == "edit" or all(path.is_file() and digest(path) == initial_hashes[path.name] for path in files)
    result["passed"] = bool(result["passed"] and result["read_only_files_unchanged"] and
                            not result["dialogs"] and not result.get("controller_diagnostics"))
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()


def run(packet_path, expected_hash):
    packet, control_files, generated_files = packet_inputs(packet_path, expected_hash)
    root = packet_path.parent
    output = root / "Inspection"
    working = root / WORK_DIRECTORY
    require(not output.exists() and not working.exists(), "choose a fresh packet without prior outputs")
    output.mkdir()
    report_path = output / "CoincidentMateResults.json"
    immutable = {path: digest(path) for path in (*control_files, *generated_files)}
    report = {
        "schema": SCHEMA, "packet_sha256": expected_hash, "oracle_sha256": packet["oracle_sha256"],
        "tool_hashes": packet["tool_hashes"], "generator_report_sha256": packet["generated"]["generator_report_sha256"],
        "started_at": time.time(), "phases": [], "passed": False, "heldout_acceptance": False,
    }

    def phase(label, entry, files, mode, saved=None):
        row = {"label": label, "mode": mode, "passed": False}
        report["phases"].append(row)
        write_json(report_path, report)
        measure_phase(packet, entry, files, row, output, mode=mode, saved=saved)
        write_json(report_path, report)
        return row

    edit = reopen = {}
    try:
        before = phase("ControlBefore", packet["control"], control_files, "control")
        if before["passed"]:
            working.mkdir()
            work_files = tuple(working / path.name for path in generated_files)
            for source, target in zip(generated_files, work_files, strict=True):
                copyfile(source, target)
                require(digest(target) == immutable[source], "generated working copy differs from its frozen input")
            edit = phase("GeneratedEdit", packet["generated"], work_files, "edit")
            if edit.get("save", {}).get("passed"):
                reopen = phase("GeneratedReopen", packet["generated"], work_files, "reopen", edit["save"])
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            phase("ControlAfter", packet["control"], control_files, "control")
        except Exception as error:
            report["control_after_exception"] = repr(error)
        rows = report["phases"]
        report["controls_healthy"] = [row["passed"] for row in rows if row["mode"] == "control"] == [True, True]
        report["frozen_inputs_unchanged"] = all(path.is_file() and digest(path) == sha for path, sha in immutable.items())
        processes = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in rows}
        report["distinct_processes"] = sum(type(value) is int and value > 0 for value in processes)
        valid_batch = bool(report["controls_healthy"] and report["frozen_inputs_unchanged"] and
                           report["distinct_processes"] == len(rows) and "exception" not in report)
        report["native_load_and_rebuild_observed"] = bool(valid_batch and edit.get("base_passed") and not edit.get("dialogs") and not edit.get("controller_diagnostics"))
        report["passed"] = bool(valid_batch and edit.get("passed") and reopen.get("passed") and len(rows) == 4)
        report["finished_at"] = time.time()
        write_json(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Measure the first generated same-path coincident mate against disclosed native controls")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    path = args.packet.resolve(strict=True)
    if args.verify_only:
        packet_inputs(path, args.packet_sha256)
        print(json.dumps({"verified_input_packet": args.packet_sha256}))
        return 0
    report = run(path, args.packet_sha256)
    print(json.dumps({key: report[key] for key in ("passed", "controls_healthy", "native_load_and_rebuild_observed", "distinct_processes")}))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
