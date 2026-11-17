from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import time
from itertools import islice
from pathlib import Path
from shutil import copyfile

from AuthorCurves import Recorder, digest, require, write_json
from InspectGeneratedCoincidentMate import (
    DIMENSIONS, SOURCE_LOCK_SHA, SOURCE_SPECS_SHA, TOOL_FILES, WORK_DIRECTORY, checked, close, configuration,
    exact_file, finite, pair_paths, plane_residual, properties, reference_comparison, scene_occurrences, valid_sha,
)


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[3]
TOOLS = (*TOOL_FILES, SCRIPT.name)
CONTROL = "A19PlaneParallel"
CHILD = "CohortChild.SLDPRT"
SCHEMA = "kit.sw2026.generated-parallel-mate-trial.v1"
WRITER_PATHS = (
    "ParallelMateBundleProcess.py", "CoincidentMateBundleProcess.py", "builders/Assembly.py",
    "builders/AssemblyDocument.py", "builders/AssemblyMateEndpoint.py", "builders/AssemblyPlanarMate.py",
)


def validate_case(case):
    require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", case["name"]) and
            re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*\.SLDPRT", case["child"]), "invalid parallel proof filenames")
    require(case["configuration"] == "Default" and case["fixed_occurrence"] == 0, "parallel proof requires fixed first occurrence and Default")
    stem = Path(case["child"]).stem
    require(case["occurrence_names"] == [stem + "-1", stem + "-2"], "unexpected parallel occurrence names")
    require(case["mates"] == [{"kind": "parallel", "name": "Parallel1", "planes": [[0, "Front Plane"], [1, "Front Plane"]]}],
            "parallel proof requires exactly the ordered Front Plane mate")
    placements = case["placements"]
    require(len(placements) == 2 and all(row["axis"] == "z" and finite(row["angle_deg"]) and len(row["translation_m"]) == 3 and
                                          all(map(finite, row["translation_m"])) for row in placements), "parallel proof requires two ordinary Z-axis placements")
    gap = placements[1]["translation_m"][2] - placements[0]["translation_m"][2]
    require(abs(gap) > 1e-5, "parallel case must distinguish preserved separation from coincidence")
    dimensions = case["dimensions_m"]
    require(case["rectangle_position"] in ("corner", "centered") and set(dimensions) == set(DIMENSIONS) and
            all(finite(value) and value > 0 for value in dimensions.values()), "invalid proof prism dimensions")
    return gap


def disclose_control(directory, stage):
    from PrepareGeneratedCoincidentMate import LOCK, SPECS, pinned_json

    lock = pinned_json(LOCK, SOURCE_LOCK_SHA, ROOT)
    specs = pinned_json(SPECS, SOURCE_SPECS_SHA, ROOT)
    require(lock["passed"] and lock["controls_healthy"] and lock["heldout_results_sealed"], "invalid planar source lock")
    source, = (row for row in lock["cases"] if row["name"] == CONTROL and row["split"] == "discovery")
    authored, = (row for row in specs["cases"] if row["name"] == CONTROL and row["split"] == "discovery")
    relative = directory.relative_to(stage.parent)
    require(relative.parts[-2:] == (CONTROL, "author") and not directory.is_relative_to(stage), "choose the disclosed A19 source directory")
    native = pinned_json(directory.parent / "fresh-reopen/Record.json", source["record_sha256"][1], directory.parent)
    phase = native["assembly_result"]
    identity = phase["oracle_identity"]
    require(native["job"]["case"] == authored and phase["passed"] and phase["source_immutable"] and phase["open_errors"] == phase["open_warnings"] == 0 and
            identity["version_matches"] and identity["sha256"] == lock["oracle_sha256"], "A19 lacks its matching clean native reopen")
    observed = phase["rebuilt"]
    case = {key: authored[key] for key in ("name", "fixed_occurrence", "placements")}
    case.update(child=CHILD, configuration="Default", rectangle_position="centered", dimensions_m=dict(zip(DIMENSIONS, (0.04, 0.02, 0.01), strict=True)),
                occurrence_names=[row["name"] for row in observed["occurrences"]], mates=[row | {"name": "Parallel1"} for row in authored["mates"]])
    gap = validate_case(case)
    require([row["occurrence"] for row in observed["mates"][0]["entities"]] == case["occurrence_names"], "A19 reference order differs from authored input")
    sources = ((CONTROL + ".SLDASM", source), (CHILD, source["synchronized_child"]))
    files = {name: {"sha256": row["native_sha256"], "bytes": row["native_bytes"]} for name, row in sources}
    pair_paths(directory, case, files)
    tree = [[row[key] for key in ("name", "type", "parent")] for row in observed["tree"]]
    return {"case": case, "gap_m": gap, "expected_tree": tree, "files": files, "relative_directory": relative.as_posix(),
            "native_reopen_sha256": source["record_sha256"][1], "initial_child_stamp": phase["reopened_child_stamp"]}, lock["oracle_sha256"]


def prepare(args):
    root = args.output.resolve()
    control_path = args.disclosed_control.resolve(strict=True)
    generated_path = args.generated.resolve(strict=True)
    require(not root.exists() and not root.is_relative_to(ROOT) and root.parent.is_dir(), "choose an unused private parallel deck")
    require(control_path != generated_path and not generated_path.is_relative_to(ROOT) and not control_path.is_relative_to(ROOT), "use separate private input directories")
    control, oracle = disclose_control(control_path, root)
    prediction = args.prediction.resolve(strict=True)
    receipt = args.generator_report.resolve(strict=True)
    case = json.loads(checked(prediction, args.prediction_sha256, owner=prediction.parent).read_bytes())
    report = json.loads(checked(receipt, args.generator_report_sha256, owner=receipt.parent).read_bytes())
    require(report["schema"] == "kit.sw2026.generated-parallel-mate-bundle.v1" and report["prediction_sha256"] == args.prediction_sha256 and
            report["writer_output_count"] == 2 and report["heldout_inputs_tested"] == report["input_runtime_file_access_attempts"] == 0 and
            report["native_acceptance"] is False, "generated pair does not match the guarded authored report")
    stem = Path(case["child"]).stem
    case = case | {"rectangle_position": "corner", "occurrence_names": [stem + "-1", stem + "-2"]}
    gap = validate_case(case)
    require(math.isclose(gap, report["inspection"]["wrappers"][1]["detached"]["world_origin"]["z"] -
                         report["inspection"]["wrappers"][0]["detached"]["world_origin"]["z"], rel_tol=0, abs_tol=1e-12),
            "authored plane separation differs from the typed writer report")
    files = {}
    for name, role in ((case["name"] + ".SLDASM", "assembly"), (case["child"], "child")):
        artifact = report[role]
        require(set(artifact) == {"bytes", "sha256", "streams"}, "require a sanitized generated report")
        files[name] = {key: artifact[key] for key in ("bytes", "sha256")}
    generated = pair_paths(generated_path, case, files)
    names = dict(zip(control["case"]["occurrence_names"], case["occurrence_names"], strict=True))
    tree = [[names.get(name, name), kind, names.get(parent, parent)] for name, kind, parent in control["expected_tree"]]
    root.mkdir()
    (root / "Tools").mkdir()
    (root / "FrozenGenerated").mkdir()
    for path in generated:
        copyfile(path, root / "FrozenGenerated" / path.name)
    copyfile(prediction, root / "AuthoredPrediction.json")
    copyfile(receipt, root / "GeneratorReport.json")
    tools = {}
    for name in TOOLS:
        path = root / "Tools" / name
        copyfile(SCRIPT.parent / name, path)
        tools[name] = digest(path)
    path = root / "Trial.json"
    write_json(path, {
        "schema": SCHEMA, "oracle_sha256": oracle, "source_lock_sha256": SOURCE_LOCK_SHA, "source_specs_sha256": SOURCE_SPECS_SHA,
        "tool_hashes": tools, "writer_tool_hashes": {name: digest(SCRIPT.parent / name) for name in WRITER_PATHS}, "control": control,
        "generated": {"case": case, "gap_m": gap, "expected_tree": tree, "files": files, "prediction_sha256": args.prediction_sha256,
                      "generator_report_sha256": args.generator_report_sha256}, "heldout_inputs_tested": 0, "native_acceptance": False,
    })
    sha = digest(path)
    subprocess.run([sys.executable, "-B", str(root / "Tools" / SCRIPT.name), "verify", str(path), "--packet-sha256", sha],
                   check=True, capture_output=True, timeout=25)
    return {"packet": str(path), "packet_sha256": sha, "observer_sha256": tools[SCRIPT.name], "writer_tool_hashes": json.loads(path.read_bytes())["writer_tool_hashes"]}


def verify(path, sha):
    require(path.name == "Trial.json" and valid_sha(sha) and digest(path) == sha, "parallel proof packet digest differs")
    root = path.parent
    packet = json.loads(path.read_bytes())
    require(packet["schema"] == SCHEMA and packet["source_lock_sha256"] == SOURCE_LOCK_SHA and packet["source_specs_sha256"] == SOURCE_SPECS_SHA and
            packet["heldout_inputs_tested"] == 0 and packet["native_acceptance"] is False, "unexpected parallel discovery provenance")
    guest = (root / "Tools").resolve(strict=True)
    require(guest == SCRIPT.parent and guest.is_relative_to(root) and set(packet["tool_hashes"]) == set(TOOLS), "run the frozen parallel tool")
    for name, expected in packet["tool_hashes"].items():
        checked(guest / name, expected, owner=guest)
    control, generated = packet["control"], packet["generated"]
    relative = Path(control["relative_directory"])
    require(not relative.anchor and ".." not in relative.parts and relative.parts[-2:] == (CONTROL, "author"), "parallel control must be disclosed A19")
    control_dir = (root.parent / relative).resolve(strict=True)
    frozen = (root / "FrozenGenerated").resolve(strict=True)
    require(control_dir.is_relative_to(root.parent) and not control_dir.is_relative_to(root) and frozen.is_relative_to(root), "parallel directory custody differs")
    for entry in (control, generated):
        require(validate_case(entry["case"]) == entry["gap_m"], "parallel gap differs from its authored placements")
    require(control["case"]["name"] == CONTROL and control["case"]["child"] == CHILD, "unexpected A19 pair")
    checked(root / "AuthoredPrediction.json", generated["prediction_sha256"], owner=root)
    checked(root / "GeneratorReport.json", generated["generator_report_sha256"], owner=root)
    return packet, pair_paths(control_dir, control["case"], control["files"]), pair_paths(frozen, generated["case"], generated["files"])


def parallel_mate(author, parent, child_path, scene):
    from AssemblyMateEvidence import DATUM_PLANE_SELECTION_TYPE, mate_features, require_plane

    features = list(islice(mate_features(author, parent), 2))
    require(len(features) == 1, "assembly does not expose one native parallel mate")
    feature, = features
    mate = author.typed(author.get(feature, "GetSpecificFeature2"), "Mate2")
    row = scene["mate"] = {"name": str(author.get(feature, "Name")), "feature_type": str(author.get(feature, "GetTypeName2")),
                           "type": int(author.get(mate, "Type")), "alignment": int(author.get(mate, "Alignment")),
                           "suppressed": bool(author.get(feature, "IsSuppressed")), "entity_count": int(author.get(mate, "GetMateEntityCount")), "entities": []}
    require(row["name"] == "Parallel1" and row["feature_type"] == "MateParallel" and row["type"] == 3 and
            row["alignment"] == 0 and not row["suppressed"] and row["entity_count"] == 2, "native parallel feature type or alignment differs")
    for index, occurrence in enumerate(scene["occurrences"]):
        entity = author.typed(author.get(mate, "MateEntity", index), "MateEntity2")
        component = author.typed(author.get(entity, "ReferenceComponent"), "Component2")
        values = [float(value) for value in author.get(entity, "EntityParams") or ()]
        model = author.get(component, "GetModelDoc2")
        endpoint = {"occurrence": str(author.get(component, "Name2")), "reference_type": int(author.get(entity, "ReferenceType2")),
                    "point": values[:3], "normal": values[3:6], "child_path_matches": bool(model is not None and exact_file(author.get(model, "GetPathName"), child_path))}
        row["entities"].append(endpoint)
        require(endpoint["occurrence"] == occurrence["name"] and endpoint["reference_type"] == DATUM_PLANE_SELECTION_TYPE and
                endpoint["child_path_matches"] and len(values) == 8 and all(map(finite, values)), "native parallel endpoint identity or type differs")
        feature = author.get(component, "FeatureByName", "Front Plane")
        require(feature is not None and author.get(feature, "GetTypeName2") == "RefPlane", "parallel endpoint's Front Plane is missing")
        require_plane(endpoint, occurrence["transform"], "Front Plane")
        endpoint["reference_comparison"] = reference_comparison(author, entity, feature)
        require(endpoint["reference_comparison"].get("plane_equality") == 1, "native endpoint does not match the exact occurrence plane object")
    first, second = row["entities"]
    row["entity_relation"] = plane_residual(first["point"], first["normal"], second["point"], second["normal"])
    first, second = (item["transform"] for item in scene["occurrences"])
    row["placement_relation"] = plane_residual(first[9:12], first[6:9], second[9:12], second[6:9])
    return row


def observe(author, parent, assembly, child_path, entry, result):
    import Swapp
    from AuthorAssemblySources import feature_tree, placement_transform, transform_point
    from ProbeAssemblyRebuild import model_state

    case = entry["case"]
    matrices = [placement_transform(spec) for spec in case["placements"]]
    result["parent_state"] = model_state(author, parent)
    child = scene_occurrences(author, assembly, child_path, case, matrices, result)
    result["child_state"] = model_state(author, child)
    result["child_stamp"] = int(author.get(child, "GetUpdateStamp"))
    result["child_dimensions_m"] = Swapp.parameters(child, DIMENSIONS)
    result["configurations"] = [configuration(author, doc) for doc in (parent, child)]
    result["parent_tree"] = feature_tree(author, parent)
    result["child_tree"] = feature_tree(author, child)
    mate = parallel_mate(author, parent, child_path, result)
    matched = all(close(mate[key]["normal_dot"], 1.0, relative=0, absolute=1e-10) and
                  close(mate[key]["signed_offset_m"], entry["gap_m"], relative=0, absolute=1e-10)
                  for key in ("entity_relation", "placement_relation"))
    target = properties(case["dimensions_m"], case["rectangle_position"])
    centers = [transform_point(matrix, target["com"]) for matrix in matrices]
    assembly_geometry = {"volume": 2 * target["volume"], "area": 2 * target["area"],
                         "com": [math.fsum(center[axis] for center in centers) / 2 for axis in range(3)]}
    result["mass_properties"] = {"child": Swapp.mass(child), "assembly": Swapp.mass(parent)}
    for key, expected in (("child", target), ("assembly", assembly_geometry)):
        actual = result["mass_properties"][key]
        require(isinstance(actual, dict) and "error" not in actual and all(close(actual.get(name), expected[name]) for name in ("volume", "area")) and
                len(actual.get("com", ())) == 3 and all(close(value, desired, absolute=1e-12) for value, desired in zip(actual["com"], expected["com"], strict=True)),
                f"native {key} geometry differs from independent prism prediction")
    result["matches"] = bool(matched and result["occurrences_match"] and result["body_count"] == 2 and
                             result["parent_state"]["whats_wrong"] == result["child_state"]["whats_wrong"] == 0 and
                             entry["expected_tree"] == [[row[key] for key in ("name", "type", "parent")] for row in result["parent_tree"]] and
                             result["configurations"] == [{"names": ["Default"], "active": "Default"}] * 2 and
                             all(close(result["child_dimensions_m"].get(key), case["dimensions_m"][key], relative=0, absolute=1e-12) for key in DIMENSIONS))


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
            identity = recorder.call("verify pinned oracle executable", application_identity, controller.app)
            row["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == packet["oracle_sha256"] and controller.revision == "34.5.2", "oracle build differs")
            author = CurveAuthor(controller.app, recorder, Swapp)
            parent, errors, warnings = recorder.call("open exact same-path parallel assembly read-only", controller.open, files[0], read_only=True)
            row.update(opened=parent is not None, open_errors=errors, open_warnings=warnings)
            require(parent is not None and exact_file(author.get(parent, "GetPathName"), files[0]), "native parent path differs")
            assembly = author.typed(parent, "AssemblyDoc")

            def capture(label):
                scene = row[label] = {"matches": False}
                try:
                    recorder.call(f"measure {label} native parallel mate", observe, author, parent, assembly, files[1], entry, scene)
                except Exception as error:
                    scene["exception"] = repr(error)
                return scene

            initial = capture("initial")
            row["forced_rebuild"] = bool(recorder.call("explicit parent rebuild", author.get, parent, "ForceRebuild3", False))
            rebuilt = capture("rebuilt")
            row["passed"] = errors == warnings == 0 and row["forced_rebuild"] and initial["matches"] and rebuilt["matches"] and (
                "initial_child_stamp" not in entry or initial["child_stamp"] == entry["initial_child_stamp"])
        except Exception as error:
            recorder.failure(error)
            row["exception"] = repr(error)
        finally:
            if controller is not None:
                if parent is not None:
                    controller.close_doc(parent)
                controller.close()
                row["controller_diagnostics"] = controller.diagnostics
    row["dialogs"] = monitor.log
    row["input_hashes_unchanged"] = all(path.is_file() and digest(path) == expected for path, expected in initial_files.items())
    row["passed"] = bool(row["passed"] and row["input_hashes_unchanged"] and not row["dialogs"] and not row.get("controller_diagnostics"))
    recorder.data.update(result=row, passed=row["passed"], finished_at=time.time())
    recorder.flush()


def run(path, sha):
    packet, control, generated = verify(path, sha)
    root = path.parent
    output, work = root / "Inspection", root / WORK_DIRECTORY
    require(not output.exists() and not work.exists(), "choose an unused parallel trial work location")
    output.mkdir()
    immutable = {file: digest(file) for file in (*control, *generated)}
    result = {"schema": SCHEMA, "packet_sha256": sha, "oracle_sha256": packet["oracle_sha256"], "tool_hashes": packet["tool_hashes"],
              "read_only": True, "heldout_acceptance": False, "phases": [], "passed": False, "started_at": time.time()}
    record = output / "ParallelMateResults.json"

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
                require(digest(target) == immutable[source], "parallel working copy differs")
            candidate = phase("Generated", packet["generated"], paths)
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        try:
            phase("ControlAfter", packet["control"], control)
        except Exception as error:
            result["control_after_exception"] = repr(error)
        result["controls_healthy"] = [row["passed"] for row in result["phases"] if row["label"].startswith("Control")] == [True, True]
        result["frozen_inputs_unchanged"] = all(path.is_file() and digest(path) == expected for path, expected in immutable.items())
        identities = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in result["phases"]}
        result["distinct_processes"] = sum(type(item) is int and item > 0 for item in identities)
        result["passed"] = bool(result["controls_healthy"] and result["frozen_inputs_unchanged"] and result["distinct_processes"] == 3 and
                                candidate.get("passed") and "exception" not in result)
        result["finished_at"] = time.time()
        write_json(record, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Freeze or run the scoped generated parallel mate native trial")
    commands = parser.add_subparsers(dest="mode", required=True)
    freezer = commands.add_parser("prepare")
    for name in ("prediction", "generator_report", "generated", "disclosed_control", "output"):
        freezer.add_argument(name, type=Path)
    for flag in ("--prediction-sha256", "--generator-report-sha256"):
        freezer.add_argument(flag, required=True)
    for mode in ("verify", "run"):
        command = commands.add_parser(mode)
        command.add_argument("packet", type=Path)
        command.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        print(json.dumps(prepare(args), sort_keys=True))
        return 0
    path = args.packet.resolve(strict=True)
    if args.mode == "verify":
        verify(path, args.packet_sha256)
        print(json.dumps({"verified_input_packet": args.packet_sha256}))
        return 0
    result = run(path, args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
