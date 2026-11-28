from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path
from shutil import copyfile

from AuthorCurves import Recorder, digest, require, write_json
from InspectGeneratedCoincidentMate import (
    CONTROL_CHILD, CONTROL_NAME, SOURCE_LOCK_SHA, SOURCE_SPECS_SHA, TOOL_FILES, WORK_DIRECTORY,
    checked, exact_file, measure_phase, observe_scene, pair_paths, valid_sha, validate_case,
)


SCRIPT = Path(__file__).resolve()
TOOLS = (*TOOL_FILES, SCRIPT.name)
ROOT = SCRIPT.parents[3]
PRIOR_RECEIPT = "59438ac9c310e9e798ebc3e0a8390e4aeefae246bed34d54cfe89f4d40ab2e81"
SCHEMA = "kit.sw2026.generated-coincident-mate-solve-trial.v1"


def solved_case(authored):
    stem = Path(authored["child"]).stem
    names = authored.get("occurrence_names", [stem + "-1", stem + "-2"])
    anchor, floating = authored["placements"]
    require(anchor["angle_deg"] == floating["angle_deg"] == 0, "solve trial requires identity basis transforms")
    first, second = anchor["translation_m"], floating["translation_m"]
    gap = second[1] - first[1]
    require(math.isfinite(gap) and abs(gap) > 1e-5, "solve trial requires a nonzero authored plane offset")
    solved = floating | {"translation_m": [second[0], first[1], second[2]]}
    result = authored | {"rectangle_position": "corner", "occurrence_names": names, "placements": [anchor, solved]}
    validate_case(result)
    return result, gap


def typed_start_pose(parent, authored):
    sys.path[:0] = [str(SCRIPT.parent / "serial"), str(ROOT / "src")]
    from AssemblyMates import load_mate_list, store_mate_list
    from AssemblySources import CONFIG, RESOLVED
    from Classes import registry
    from Core import DOCUMENT_VERSION_2026
    from defs.ConfigPart import load_config
    from defs.ResolvedCore import load_resolved
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    mates_name = CONFIG + "-MatesList"
    version = DOCUMENT_VERSION_2026
    rules = registry()
    archive = SldprtArchive.from_bytes(parent.read_bytes(), parent)
    config, config_reader = load_config(archive.require(CONFIG), rules, version, archive=archive, name=CONFIG)
    resolved, resolved_reader = load_resolved(archive.require(RESOLVED), rules, version, archive=archive,
                                             name=RESOLVED, seed=config_reader.map_state())
    inherited = resolved_reader.map_state()
    mate_bytes = archive.require(mates_name)
    (mate,), _ = load_mate_list(mate_bytes, rules, version, resolved_map=inherited)
    require(not config.tail and not resolved.tail and store_mate_list((mate,), rules, version, resolved_map=inherited) == mate_bytes,
            "offset archive failed typed mate readback")
    parent_model, = config.roots
    occurrences = [item["o"] for item in parent_model["f68"]["list"]["items"]]
    require(parent_model.cls == "moAssembly_c" and mate.cls == "moMateCoincident" and mate["f3b4"] == 1 and
            mate["f0c"] == 1 and mate["f3b8"] == 0 and [row["f400"] for row in occurrences] == [3, 3] and
            [row["f408"] for row in occurrences] == [1, 0], "offset writer changed the admitted pending mate state")
    frames = []
    for occurrence, wrapper, detached, request in zip(occurrences, mate["f410"], mate["f3c8"], authored["placements"], strict=True):
        placement = occurrence["f360"]
        plane = wrapper["o"]
        origin = [plane["fd0"][key] for key in "xyz"]
        normal = [plane["fe8"][key] for key in "xyz"]
        offset = [placement[key] for key in ("f58", "f60", "f68")]
        require(not placement["has_matrix"] and plane["f10"] == plane["f18"] == placement and normal == [0.0, 1.0, 0.0] and
                offset == origin == request["translation_m"], "offset occurrence or wrapper does not preserve the authored plane frame")
        require(all(plane[key] == detached["o"][key] for key in ("fd0", "fe8")), "detached plane differs from its resolved mate endpoint")
        frames.append({"occurrence_id": occurrence["f08"], "stored_translation_m": offset, "wrapper_origin_m": origin,
                       "wrapper_normal": normal, "detached_frame_matches": True})
    return {"version": version, "mate_id": mate["f08"], "mate_pending_word": mate["f0c"], "mate_solve_state": mate["f3b8"],
            "frames": frames, "parent_sha256": digest(parent), "mate_list_sha256": sha256(mate_bytes).hexdigest()}


def verify(path, expected):
    require(path.name == "Trial.json" and valid_sha(expected) and digest(path) == expected, "solve packet digest differs")
    root = path.parent
    tools = (root / "Tools").resolve(strict=True)
    require(tools == SCRIPT.parent and tools.is_relative_to(root), "run the frozen solve tool")
    packet = json.loads(path.read_bytes())
    require(packet["schema"] == SCHEMA and packet["source_lock_sha256"] == SOURCE_LOCK_SHA and packet["source_specs_sha256"] == SOURCE_SPECS_SHA and
            packet["prior_native_receipt_sha256"] == PRIOR_RECEIPT and packet["heldout_inputs_tested"] == 0 and packet["native_acceptance"] is False,
            "unexpected off-plane discovery provenance")
    require(set(packet["tool_hashes"]) == set(TOOLS), "solve tool inventory differs")
    for name, sha in packet["tool_hashes"].items():
        checked(tools / name, sha, owner=tools)
    entry, control = packet["generated"], packet["control"]
    prediction_path = checked(root / "AuthoredPrediction.json", entry["authored_prediction_sha256"], owner=root)
    checked(root / "GeneratorReport.json", entry["generator_report_sha256"], owner=root)
    authored = json.loads(prediction_path.read_bytes())
    case, gap = solved_case(authored)
    require(entry["case"] == case and entry["stored_gap_m"] == gap and entry["authored_placements"] == authored["placements"],
            "packet disagrees with the frozen authored and solved placements")
    frozen = (root / "FrozenGenerated").resolve(strict=True)
    relative = Path(control["relative_directory"])
    require(not relative.anchor and ".." not in relative.parts and relative.parts[-2:] == (CONTROL_NAME, "author"), "solve trial must bracket with A17")
    control_dir = (root.parent / relative).resolve(strict=True)
    require(frozen.is_relative_to(root) and control_dir.is_relative_to(root.parent) and not control_dir.is_relative_to(root), "solve directories overlap or escape custody")
    require(control["case"]["name"] == CONTROL_NAME and control["case"]["child"] == CONTROL_CHILD, "unexpected A17 file or case names")
    generated_files = pair_paths(frozen, case, entry["files"])
    typed = entry["typed_start"]
    require(typed["parent_sha256"] == digest(generated_files[0]) and
            [frame["stored_translation_m"] for frame in typed["frames"]] == [item["translation_m"] for item in authored["placements"]],
            "stored-pose typed receipt disagrees with the frozen bytes")
    return packet, pair_paths(control_dir, control["case"], control["files"]), generated_files


def prepare(args):
    from PrepareGeneratedCoincidentMate import control_source

    output = args.output.resolve()
    require(not output.exists() and not output.is_relative_to(ROOT) and output.parent.is_dir(), "choose an unused private solve deck")
    control_dir = args.disclosed_control.resolve(strict=True)
    generated_dir = args.generated.resolve(strict=True)
    require(control_dir != generated_dir and not control_dir.is_relative_to(ROOT) and not generated_dir.is_relative_to(ROOT), "use separate private control and generated directories")
    control, identity = control_source(control_dir, output)
    prior_path = ROOT / "re/solidworks/measurements/2026/GeneratedCoincidentMateNative01.json"
    prior = json.loads(checked(prior_path, PRIOR_RECEIPT, owner=ROOT).read_bytes())
    require(prior["passed"] and prior["controls_healthy"] and prior["oracle_sha256"] == identity, "first aligned mate has no matching native proof")
    prediction_path = args.prediction.resolve(strict=True)
    report_path = args.generator_report.resolve(strict=True)
    authored = json.loads(checked(prediction_path, args.prediction_sha256, owner=prediction_path.parent).read_bytes())
    report = json.loads(checked(report_path, args.generator_report_sha256, owner=report_path.parent).read_bytes())
    case, gap = solved_case(authored)
    require(re.fullmatch(r"[0-9a-f]{40}", args.writer_revision) and report["schema"] == "kit.sw2026.generated-coincident-mate-bundle.v1" and
            report["native_acceptance"] is False and report["input_runtime_file_access_attempts"] == report["heldout_inputs_tested"] == 0 and
            report["writer_output_count"] == 2 and report["prediction_sha256"] == args.prediction_sha256,
            "offset pair has no matching independently authored generator proof")
    names = (case["name"] + ".SLDASM", case["child"])
    files = {}
    for filename, role in zip(names, ("assembly", "child"), strict=True):
        artifact = report[role]
        require(set(artifact) == {"bytes", "sha256", "streams"} and artifact["bytes"] > 0, "require a sanitized generated artifact receipt")
        files[filename] = {key: artifact[key] for key in ("bytes", "sha256")}
    source_paths = pair_paths(generated_dir, case, files)
    stored = typed_start_pose(source_paths[0], authored)
    name_map = dict(zip(control["case"]["occurrence_names"], case["occurrence_names"], strict=True))
    tree = [[name_map.get(name, name), kind, name_map.get(parent, parent)] for name, kind, parent in control["expected_tree"]]
    output.mkdir()
    (output / "Tools").mkdir()
    (output / "FrozenGenerated").mkdir()
    for source in source_paths:
        copyfile(source, output / "FrozenGenerated" / source.name)
    copyfile(prediction_path, output / "AuthoredPrediction.json")
    copyfile(report_path, output / "GeneratorReport.json")
    source_tools = {}
    for name in TOOLS:
        target = output / "Tools" / name
        copyfile(SCRIPT.parent / name, target)
        source_tools[name] = digest(target)
    packet_path = output / "Trial.json"
    write_json(packet_path, {
        "schema": SCHEMA, "source_lock_sha256": SOURCE_LOCK_SHA, "source_specs_sha256": SOURCE_SPECS_SHA,
        "native_acceptance": False, "heldout_inputs_tested": 0, "oracle_sha256": identity,
        "prior_native_receipt_sha256": PRIOR_RECEIPT, "tool_hashes": source_tools, "control": control,
        "generated": {"case": case, "expected_tree": tree, "authored_placements": authored["placements"], "stored_gap_m": gap,
                      "typed_start": stored, "files": files, "authored_prediction_sha256": args.prediction_sha256,
                      "generator_report_sha256": args.generator_report_sha256, "writer_revision": args.writer_revision},
    })
    sha = digest(packet_path)
    subprocess.run([sys.executable, "-B", str(output / "Tools" / SCRIPT.name), "verify", str(packet_path), "--packet-sha256", sha],
                   check=True, capture_output=True, timeout=25)
    return {"packet": str(packet_path), "packet_sha256": sha, "observer_sha256": source_tools[SCRIPT.name], "typed_start_pose": stored}


def classify_pose(scene, expected):
    from AuthorAssemblySources import transform_matches

    rows = scene.get("occurrences", ())
    if len(rows) != 2:
        return "unavailable"
    for label, matrices in expected.items():
        if all(transform_matches(row["transform"], transform) for row, transform in zip(rows, matrices, strict=True)):
            return label
    return "unexpected"


def exact_mate(scene):
    mate = scene.get("mate", {})
    return bool(mate.get("matches") and len(mate["entities"]) == 2 and
                all(row["reference_comparison"].get("plane_equality") == 1 for row in mate["entities"]))


def observe_offset_phase(packet, files, output, result):
    import Swapp
    from AuthorAssemblySources import placement_transform
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    entry = packet["generated"]
    parent_path, child_path = files
    expected = {
        "stored": [placement_transform(row) for row in entry["authored_placements"]],
        "solved": [placement_transform(row) for row in entry["case"]["placements"]],
    }
    result.update(input_sha256={path.name: digest(path) for path in files}, correction_observed=False, correction_phase=None)
    recorder = Recorder(output / "GeneratedSolveCalls.json", {"lane": "same-path read-only offset solve"})
    controller = parent = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = recorder.call("verify pinned SOLIDWORKS executable", application_identity, controller.app)
            result["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == packet["oracle_sha256"] and controller.revision == "34.5.2", "oracle build differs")
            author = CurveAuthor(controller.app, recorder, Swapp)
            parent, errors, warnings = recorder.call("open exact offset assembly read-only", controller.open, parent_path, read_only=True)
            result.update(opened=parent is not None, open_errors=errors, open_warnings=warnings)
            require(parent is not None and exact_file(author.get(parent, "GetPathName"), parent_path), "native open did not resolve the expected offset assembly")
            assembly = author.typed(parent, "AssemblyDoc")

            def capture(label):
                scene = result[label] = {"passed": False}
                try:
                    recorder.call(f"measure {label} offset assembly and mate", observe_scene, author, parent, assembly,
                                  child_path, entry, entry["case"]["dimensions_m"], scene)
                except Exception as error:
                    scene["exception"] = repr(error)
                scene["pose"] = classify_pose(scene, expected)
                scene["exact_solved_mate"] = exact_mate(scene)
                return scene

            initial = capture("initial")
            result["forced_rebuild"] = bool(recorder.call("force first explicit parent rebuild", author.get, parent, "ForceRebuild3", False))
            rebuilt = capture("rebuilt")
            final_solved = rebuilt["pose"] == "solved" and rebuilt["passed"] and rebuilt["exact_solved_mate"] and result["forced_rebuild"]
            if final_solved and initial["pose"] == "stored":
                result["correction_phase"] = "explicit_rebuild"
            if final_solved and initial["pose"] == "solved" and initial["passed"] and initial["exact_solved_mate"]:
                result["correction_phase"] = "open"
            result["correction_observed"] = result["correction_phase"] is not None
            result["passed"] = errors == warnings == 0 and result["correction_observed"]
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
    result["immutable"] = all(path.is_file() and digest(path) == result["input_sha256"][path.name] for path in files)
    result["passed"] = bool(result["passed"] and result["immutable"] and not result["dialogs"] and not result.get("controller_diagnostics"))
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()


def run(path, expected):
    packet, controls, candidates = verify(path, expected)
    root = path.parent
    output = root / "Inspection"
    working = root / WORK_DIRECTORY
    require(not output.exists() and not working.exists(), "choose a clean frozen offset trial")
    output.mkdir()
    initial_digests = {file: digest(file) for file in (*controls, *candidates)}
    evidence = output / "CoincidentMateSolveResults.json"
    report = {"schema": SCHEMA, "packet_sha256": expected, "oracle_sha256": packet["oracle_sha256"],
              "tool_hashes": packet["tool_hashes"], "typed_start": packet["generated"]["typed_start"],
              "heldout_acceptance": False, "phases": [], "started_at": time.time(), "passed": False}

    def stage(label, action):
        phase = {"label": label, "passed": False}
        report["phases"].append(phase)
        write_json(evidence, report)
        action(phase)
        write_json(evidence, report)
        return phase

    def control(label):
        return stage(label, lambda row: measure_phase(packet, packet["control"], controls, row, output, mode="control"))

    solve = {}
    try:
        before = control("ControlBefore")
        if before["passed"]:
            working.mkdir()
            work = tuple(working / file.name for file in candidates)
            for source, destination in zip(candidates, work, strict=True):
                copyfile(source, destination)
                require(digest(destination) == initial_digests[source], "offset working copy differs from the immutable generated input")
            solve = stage("GeneratedSolve", lambda row: observe_offset_phase(packet, work, output, row))
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        after = {}
        try:
            after = control("ControlAfter")
        except Exception as error:
            report["control_after_exception"] = repr(error)
        report["controls_healthy"] = [phase["passed"] for phase in report["phases"] if phase["label"].startswith("Control")] == [True, True]
        report["frozen_inputs_unchanged"] = all(file.is_file() and digest(file) == sha for file, sha in initial_digests.items())
        processes = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in report["phases"]}
        report["distinct_processes"] = sum(type(item) is int and item > 0 for item in processes)
        credible = bool(after.get("passed") and report["controls_healthy"] and report["frozen_inputs_unchanged"] and
                        report["distinct_processes"] == 3 and solve.get("immutable") and not solve.get("dialogs") and
                        not solve.get("controller_diagnostics") and "exception" not in report)
        report["active_placement_correction_observed"] = bool(credible and solve.get("correction_observed"))
        report["correction_phase"] = solve.get("correction_phase") if report["active_placement_correction_observed"] else None
        report["passed"] = bool(credible and solve.get("passed"))
        report["finished_at"] = time.time()
        write_json(evidence, report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Freeze or measure the native SOLIDWORKS coincident mate from an authored off-plane start")
    subcommands = parser.add_subparsers(dest="mode", required=True)
    freezer = subcommands.add_parser("prepare")
    for name in ("prediction", "generator_report", "generated", "disclosed_control", "output"):
        freezer.add_argument(name, type=Path)
    for flag in ("--prediction-sha256", "--generator-report-sha256", "--writer-revision"):
        freezer.add_argument(flag, required=True)
    for mode in ("verify", "run"):
        command = subcommands.add_parser(mode)
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
    report = run(path, args.packet_sha256)
    print(json.dumps({key: report[key] for key in ("passed", "controls_healthy", "active_placement_correction_observed", "correction_phase")}))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
