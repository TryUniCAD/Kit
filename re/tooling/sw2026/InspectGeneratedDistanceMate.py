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
from InspectGeneratedCoincidentMate import (
    DIMENSIONS, SOURCE_LOCK_SHA, SOURCE_SPECS_SHA, TOOL_FILES, WORK_DIRECTORY,
    checked, close, configuration, exact_file, finite, pair_paths, plane_residual,
    properties, reference_comparison, scene_occurrences, valid_sha,
)


SCRIPT = Path(__file__).resolve()
SCHEMA = "kit.sw2026.generated-distance-mate-open-trial.v1"
TOOLS = (*TOOL_FILES, SCRIPT.name)
CONTROL = "A18PlaneDistance"
CONTROL_CHILD = "CohortChild.SLDPRT"
CANDIDATE = "DistanceMateDiscovery"
CANDIDATE_CHILD = "DistanceDatumPlate.SLDPRT"
PLANE = "Right Plane"
MATE = "Distance1"
CONTROL_DIRECTORY = Path("AssemblyMateSource02/A18PlaneDistance/author")
SOURCE_ARTIFACTS = ("Request.json", "Prediction.json", "GeneratorReport.json", "StructuralReceipt.json")
ORACLE_VERSION = "34.5.2.0604"
TOLERANCE = 1e-10


def distance(case):
    return case["mates"][0]["distance_m"]


def gap(case):
    return case["placements"][1]["translation_m"][0]


def validate_case(case):
    stem = Path(case["child"]).stem
    require(re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", case["name"]) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*\.SLDPRT", case["child"]),
            "invalid distance proof filenames")
    require(case["split"] == "discovery" and case["configuration"] == "Default" and case["fixed_occurrence"] == 0
            and case["occurrence_names"] == [stem + "-1", stem + "-2"], "distance proof requires two ordered Default occurrences and a fixed first occurrence")
    mate, = case["mates"]
    require(mate == {"name": MATE, "kind": "distance", "planes": [[0, PLANE], [1, PLANE]], "distance_m": distance(case)}
            and finite(distance(case)) and distance(case) > 0, "distance proof requires one positive ordered Right Plane mate")
    first, second = case["placements"]
    require(first["axis"] in ("x", "y", "z") and first["angle_deg"] == 0.0 and first["translation_m"] == [0.0, 0.0, 0.0]
            and second["axis"] == "x" and finite(second["angle_deg"]) and len(second["translation_m"]) == 3
            and all(map(finite, second["translation_m"])), "distance proof requires an identity anchor and an X-axis moving occurrence")
    sizes = case["dimensions_m"]
    require(case["rectangle_position"] in ("centered", "corner") and set(sizes) == set(DIMENSIONS)
            and all(finite(value) and value > 0 for value in sizes.values()), "invalid distance proof prism")
    require(min(gap(case), distance(case)) > sizes[DIMENSIONS[0]], "analytical assembly mass requires disjoint solids along X")


def verify(path, sha):
    root = path.parent
    checked(path, sha, owner=root)
    require(path.name == "Trial.json", "unexpected packet basename")
    packet = json.loads(path.read_bytes())
    require(packet["schema"] == SCHEMA and packet["source_lock_sha256"] == SOURCE_LOCK_SHA and packet["source_specs_sha256"] == SOURCE_SPECS_SHA
            and valid_sha(packet["oracle_sha256"]) and packet["oracle_file_version"] == ORACLE_VERSION
            and packet["read_only"] is True and packet["heldout_inputs_tested"] == 0 and packet["native_acceptance"] is False,
            "unexpected distance trial provenance")
    guest = (root / "Tools").resolve(strict=True)
    require(guest == SCRIPT.parent and guest.is_relative_to(root) and set(packet["tool_hashes"]) == set(TOOLS), "run the exact frozen guest runner")
    for name, expected in packet["tool_hashes"].items():
        checked(guest / name, expected, owner=guest)
    generated, control = (packet[label] for label in ("generated", "control"))
    for entry in (generated, control):
        validate_case(entry["case"])
    require((control["case"]["name"], control["case"]["child"]) == (CONTROL, CONTROL_CHILD) and control["relative_directory"] == CONTROL_DIRECTORY.as_posix()
            and (generated["case"]["name"], generated["case"]["child"]) == (CANDIDATE, CANDIDATE_CHILD), "distance trial pair identity differs")
    control_dir = (root.parent / CONTROL_DIRECTORY).resolve(strict=True)
    frozen = (root / "FrozenGenerated").resolve(strict=True)
    require(control_dir == root.parent / CONTROL_DIRECTORY and frozen == root / "FrozenGenerated", "distance trial directory custody differs")
    checked(control_dir.parent / "fresh-reopen/Record.json", control["native_reopen_sha256"], owner=control_dir.parent)
    require(set(generated["source_artifact_sha256"]) == set(SOURCE_ARTIFACTS), "distance writer proof inventory differs")
    for name, expected in generated["source_artifact_sha256"].items():
        checked(root / name, expected, owner=root)
    require(re.fullmatch(r"[0-9a-f]{40}", generated["writer_revision"]) and len(generated["writer_tool_hashes"]) == 14
            and all(map(valid_sha, generated["writer_tool_hashes"].values())), "distance writer source identity differs")
    require(generated["authored_gap_m"] == gap(generated["case"]) and gap(generated["case"]) != distance(generated["case"])
            and math.isclose(generated["planned_edit_target_m"] - distance(generated["case"]), 0.01675, rel_tol=0, abs_tol=1e-14),
            "distance trial must discriminate the stored and solved poses")
    return packet, pair_paths(control_dir, control["case"], control["files"]), pair_paths(frozen, generated["case"], generated["files"])


def pose_matrices(case, solved):
    from AuthorAssemblySources import placement_transform

    first, second = (placement_transform(spec) for spec in case["placements"])
    if solved:
        second[9] = first[9] + distance(case)
    return [first, second]


def classify_pose(matrices, case):
    from AuthorAssemblySources import transform_matches

    for label in ("solved", "stored"):
        if all(transform_matches(actual, expected) for actual, expected in zip(matrices, pose_matrices(case, label == "solved"), strict=True)):
            return label
    return "other"


def first_pose(author, assembly, case):
    seen = {}
    components = author.get(assembly, "GetComponents", True) or ()
    require(len(components) == 2, "first observation does not resolve two components")
    for raw in components:
        component = author.typed(raw, "Component2")
        name = str(author.get(component, "Name2"))
        require(name in case["occurrence_names"] and name not in seen, "first observation returned an unexpected component")
        value = author.typed(author.get(component, "Transform2"), "MathTransform")
        seen[name] = [float(item) for item in author.get(value, "ArrayData")]
    matrices = [seen[name] for name in case["occurrence_names"]]
    return {"pose": classify_pose(matrices, case), "transforms": matrices}


def native_distance(author, parent, child_path, case, scene):
    from AssemblyMateEvidence import DATUM_PLANE_SELECTION_TYPE, TYPES, mate_features, require_plane

    features = list(islice(mate_features(author, parent), 2))
    require(len(features) == 1, "native mate group does not contain exactly one mate")
    feature, = features
    mate = author.typed(author.get(feature, "GetSpecificFeature2"), "Mate2")
    row = scene["mate"] = {
        "name": str(author.get(feature, "Name")), "feature_type": str(author.get(feature, "GetTypeName2")),
        "type": int(author.get(mate, "Type")), "alignment": int(author.get(mate, "Alignment")),
        "suppressed": bool(author.get(feature, "IsSuppressed")), "flipped": bool(author.get(mate, "Flipped")),
        "entity_count": int(author.get(mate, "GetMateEntityCount")), "entities": [],
    }
    require((row["name"], row["feature_type"], row["type"], row["alignment"], row["entity_count"]) == (MATE, "MateDistanceDim", TYPES["distance"], 0, 2)
            and not row["suppressed"] and not row["flipped"], "native distance feature, alignment or orientation differs")
    display = author.get(feature, "GetFirstDisplayDimension")
    require(display is not None, "native distance has no display dimension")
    dimension = author.get(display, "GetDimension2", 0)
    require(dimension is not None, "native distance has no value dimension")
    row["dimension_name"] = str(author.get(dimension, "FullName"))
    row["dimension_m"] = float(author.get(dimension, "SystemValue"))
    require(row["dimension_name"] == f"D1@{MATE}@{case['name']}.Assembly" and close(row["dimension_m"], distance(case), relative=0, absolute=1e-12),
            "native assembly D1 identity or value differs")
    for index, occurrence in enumerate(scene["occurrences"]):
        entity = author.typed(author.get(mate, "MateEntity", index), "MateEntity2")
        component = author.typed(author.get(entity, "ReferenceComponent"), "Component2")
        model = author.get(component, "GetModelDoc2")
        values = [float(value) for value in author.get(entity, "EntityParams") or ()]
        endpoint = {
            "occurrence": str(author.get(component, "Name2")), "reference_type": int(author.get(entity, "ReferenceType2")),
            "point": values[:3], "normal": values[3:6], "child_path_matches": bool(model is not None and exact_file(author.get(model, "GetPathName"), child_path)),
        }
        row["entities"].append(endpoint)
        require(endpoint["occurrence"] == occurrence["name"] and endpoint["reference_type"] == DATUM_PLANE_SELECTION_TYPE
                and endpoint["child_path_matches"] and len(values) == 8 and all(map(finite, values)), "native distance endpoint identity or type differs")
        plane = author.get(component, "FeatureByName", PLANE)
        require(plane is not None and author.get(plane, "GetTypeName2") == "RefPlane", "distance endpoint's occurrence plane is missing")
        endpoint["reference_comparison"] = comparison = reference_comparison(author, entity, plane)
        require(comparison.get("plane_equality", comparison.get("feature_equality")) == 1, "native distance endpoint object differs from the occurrence's Right Plane")
        require_plane(endpoint, occurrence["transform"], PLANE)
    first, second = row["entities"]
    row["entity_relation"] = plane_residual(first["point"], first["normal"], second["point"], second["normal"])
    first, second = (item["transform"] for item in scene["occurrences"])
    row["placement_relation"] = plane_residual(first[9:12], first[:3], second[9:12], second[:3])
    return row


def mass_matches(actual, expected):
    return isinstance(actual, dict) and "error" not in actual and all(close(actual.get(key), expected[key]) for key in ("volume", "area")) and (
        len(actual.get("com", ())) == 3 and all(close(value, target, absolute=1e-12) for value, target in zip(actual["com"], expected["com"], strict=True))
    )


def observe(author, parent, assembly, child_path, entry, phase, snapshot, scene):
    import Swapp
    from AuthorAssemblySources import feature_tree, transform_point
    from ProbeAssemblyRebuild import model_state

    case = entry["case"]
    scene["parent_state"] = model_state(author, parent)
    solved = phase == "rebuilt" or snapshot["pose"] == "solved" or case["name"] == CONTROL
    matrices = pose_matrices(case, solved)
    child = scene_occurrences(author, assembly, child_path, case, matrices, scene)
    if phase == "initial" and not solved and classify_pose([row["transform"] for row in scene["occurrences"]], case) == "solved":
        scene["pose_changed_during_initial_observation"] = True
        scene["first_occurrences"] = scene.pop("occurrences")
        solved = True
        matrices = pose_matrices(case, solved)
        child = scene_occurrences(author, assembly, child_path, case, matrices, scene)
    scene["pose"] = classify_pose([row["transform"] for row in scene["occurrences"]], case)
    scene["child_state"] = model_state(author, child)
    scene["child_stamp"] = int(author.get(child, "GetUpdateStamp"))
    scene["child_dimensions_m"] = Swapp.parameters(child, DIMENSIONS)
    scene["configurations"] = [configuration(author, doc) for doc in (parent, child)]
    scene["parent_tree"], scene["child_tree"] = (feature_tree(author, doc) for doc in (parent, child))
    mate = native_distance(author, parent, child_path, case, scene)
    target = properties(case["dimensions_m"], case["rectangle_position"])
    centers = [transform_point(matrix, target["com"]) for matrix in matrices]
    assembly_target = {
        "volume": 2 * target["volume"], "area": 2 * target["area"],
        "com": [math.fsum(center[axis] for center in centers) / 2 for axis in range(3)],
    }
    scene["expected_mass_properties"] = {"child": target, "assembly": assembly_target}
    scene["mass_properties"] = {"child": Swapp.mass(child), "assembly": Swapp.mass(parent)}
    expected_gap = distance(case) if solved else gap(case)
    scene["checks"] = checks = {
        "pose": scene["pose"] == ("solved" if solved else "stored") and (phase == "rebuilt" or snapshot["pose"] in ("solved", "stored")),
        "occurrences_and_anchor": scene["occurrences_match"] and scene["body_count"] == 2,
        "plane_offsets": all(close(mate[key]["normal_dot"], 1.0, relative=0, absolute=TOLERANCE)
                             and close(mate[key]["signed_offset_m"], expected_gap, relative=0, absolute=TOLERANCE)
                             for key in ("entity_relation", "placement_relation")),
        "configurations": scene["configurations"] == [{"names": ["Default"], "active": "Default"}] * 2,
        "clean_feature_tree": [[row[key] for key in ("name", "type", "parent")] for row in scene["parent_tree"]] == entry["expected_tree"],
        "child_feature_identity": [[row["name"], row["type"]] for row in scene["child_tree"] if row["name"] in ("Sketch1", "Boss-Extrude1")]
                                  == [["Sketch1", "ProfileFeature"], ["Boss-Extrude1", "Extrusion"]],
        "child_dimensions": all(close(scene["child_dimensions_m"].get(name), case["dimensions_m"][name], relative=0, absolute=1e-12) for name in DIMENSIONS),
        "rebuild_status": all(state["whats_wrong"] == 0 and (phase == "initial" or state["needs_rebuild"] == 0)
                              for state in (scene["parent_state"], scene["child_state"])),
        "analytical_geometry": all(mass_matches(scene["mass_properties"][key], wanted) for key, wanted in scene["expected_mass_properties"].items()),
    }
    scene["matches"] = all(checks.values())


def capture(recorder, label, author, parent, assembly, child, entry, row):
    scene = row[label] = {"matches": False}
    try:
        recorder.call(f"capture {label} native distance", observe, author, parent, assembly, child, entry, label, row["first_pose"], scene)
    except Exception as error:
        scene["exception"] = repr(error)
    return scene


def measure(packet, entry, files, output, row):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    recorder = Recorder(output / (row["label"] + "Calls.json"), {"lane": row["label"], "read_only": True})
    controller = parent = None
    initial_files = {path: digest(path) for path in files}
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = row["oracle_identity"] = recorder.call("verify pinned oracle executable", application_identity, controller.app)
            require(identity["version_matches"] and identity["file_version"] == ORACLE_VERSION and identity["sha256"] == packet["oracle_sha256"]
                    and identity["process_id"] == controller.process_id and controller.revision == "34.5.2", "oracle build or ownership differs")
            author = CurveAuthor(controller.app, recorder, Swapp)
            parent, errors, warnings = recorder.call("open exact assembly read-only", controller.open, files[0], read_only=True)
            row.update(opened=parent is not None, open_errors=errors, open_warnings=warnings, opened_path=str(files[0]))
            require(parent is not None and exact_file(author.get(parent, "GetPathName"), files[0]), "native parent path differs")
            assembly = author.typed(parent, "AssemblyDoc")
            row["first_pose"] = recorder.call("first occurrence transforms after open", first_pose, author, assembly, entry["case"])
            initial = capture(recorder, "initial", author, parent, assembly, files[1], entry, row)
            row["forced_rebuild"] = bool(recorder.call("rebuild full assembly", author.get, parent, "ForceRebuild3", False))
            rebuilt = capture(recorder, "rebuilt", author, parent, assembly, files[1], entry, row)
            row["passed"] = errors == warnings == 0 and row["forced_rebuild"] and initial["matches"] and rebuilt["matches"] and (
                "initial_child_stamp" not in entry or initial["child_stamp"] == entry["initial_child_stamp"]
            )
        except Exception as error:
            recorder.failure(error)
            row["exception"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if parent is not None:
                        recorder.call("close exact document", controller.close_doc, parent)
                finally:
                    try:
                        recorder.call("exit owned oracle", controller.close)
                    finally:
                        row["controller_diagnostics"] = controller.diagnostics
    row.update(dialogs=monitor.log, progress_windows=monitor.progress)
    row["input_hashes_unchanged"] = all(path.is_file() and digest(path) == expected for path, expected in initial_files.items())
    row["passed"] = bool(row["passed"] and row["input_hashes_unchanged"] and not row["dialogs"] and not row.get("controller_diagnostics")
                         and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"])
    recorder.data.update(result=row, passed=row["passed"], finished_at=time.time())
    recorder.flush()


def run(path, sha):
    packet, control, generated = verify(path, sha)
    root = path.parent
    output, work = root / "Inspection", root / WORK_DIRECTORY
    require(not output.exists() and not output.is_symlink() and not work.exists() and not work.is_symlink(), "choose unused distance trial output and work directories")
    output.mkdir()
    immutable = {file: digest(file) for file in (*control, *generated)}
    result = {
        "schema": SCHEMA, "packet_sha256": sha, "oracle_sha256": packet["oracle_sha256"], "tool_hashes": packet["tool_hashes"],
        "writer_revision": packet["generated"]["writer_revision"], "read_only": True, "phases": [], "passed": False,
        "driving_edit_tested": False, "persistence_tested": False, "heldout_inputs_tested": 0, "heldout_acceptance": False,
        "native_acceptance": False, "started_at": time.time(),
    }
    record = output / "DistanceMateResults.json"

    def phase(label, entry, files):
        row = {"label": label, "passed": False}
        result["phases"].append(row)
        write_json(record, result)
        measure(packet, entry, files, output, row)
        write_json(record, result)
        return row

    candidate = {}
    try:
        if phase("ControlBefore", packet["control"], control)["passed"]:
            work.mkdir()
            paths = tuple(work / file.name for file in generated)
            for source, target in zip(generated, paths, strict=True):
                copyfile(source, target)
                require(digest(target) == immutable[source], "generated working copy differs")
            candidate = phase("Generated", packet["generated"], paths)
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        try:
            phase("ControlAfter", packet["control"], control)
        except Exception as error:
            result["control_after_exception"] = repr(error)
        result["controls_healthy"] = [row["passed"] for row in result["phases"] if row["label"].startswith("Control")] == [True, True]
        result["frozen_inputs_unchanged"] = all(file.is_file() and digest(file) == expected for file, expected in immutable.items())
        try:
            verify(path, sha)
            result["frozen_packet_unchanged"] = True
        except Exception as error:
            result["frozen_packet_unchanged"] = False
            result["final_packet_verification_error"] = repr(error)
        identities = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in result["phases"]}
        result["distinct_processes"] = sum(type(value) is int and value > 0 for value in identities)
        result["passed"] = bool(result["controls_healthy"] and result["frozen_inputs_unchanged"] and result["frozen_packet_unchanged"]
                                and result["distinct_processes"] == 3
                                and candidate.get("passed") and "exception" not in result)
        result["finished_at"] = time.time()
        write_json(record, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Verify or run the read-only generated distance mate trial")
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    path = args.packet.resolve(strict=True)
    if args.mode == "verify":
        verify(path, args.packet_sha256)
        print(json.dumps({"verified_input_packet": args.packet_sha256}))
        return 0
    report = run(path, args.packet_sha256)
    print(json.dumps({key: report[key] for key in ("passed", "controls_healthy", "distinct_processes")}))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
