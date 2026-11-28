from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj
import sys
import time

from AuthorCurves import Recorder, digest, require, write_json
import InspectGeneratedDistanceMate as baseline


SCRIPT = Path(__file__).resolve()
SCHEMA = "kit.sw2026.generated-distance-mate-exact-paths.v1"
BASE_PACKET = "fc150e226e7c18467e17d73a55404e93868df1a63f870e7a00455810e37e5087"
BASE_RESULT = "0678806bfc037f17689f90d0735d50b3871699b79283254389b3403470192ba3"
ORACLE_FOLDER = PureWindowsPath("C:/Users/Public/Documents/KitOracle")
FILE_NOT_FOUND = 2


def verify(path, sha):
    root = path.parent
    baseline.checked(path, sha, owner=root)
    require(path.name == "EncodedPaths.json" and SCRIPT.parent == root / "Tools", "use the frozen exact-path runner")
    plan = json.loads(path.read_bytes())
    require(plan["schema"] == SCHEMA and plan["baseline_packet_sha256"] == BASE_PACKET and plan["baseline_native_result_sha256"] == BASE_RESULT
            and plan["read_only"] is True and plan["heldout_inputs_tested"] == 0 and plan["native_acceptance"] is False,
            "unexpected exact-path trial provenance")
    baseline.checked(SCRIPT, plan["observer_sha256"], owner=root / "Tools")
    packet, control, frozen = baseline.verify(root / "Trial.json", BASE_PACKET)
    require(plan["generated_files"] == packet["generated"]["files"], "encoded path plan differs from the guarded writer bytes")
    paths = plan["encoded_paths_by_file"]
    require(set(paths) == {source.name for source in frozen}
            and all(PureWindowsPath(paths[source.name]) == ORACLE_FOLDER / source.name for source in frozen),
            "encoded targets must be the exact two guarded output files")
    return plan, packet, control, frozen


def exclusive_targets(plan, sources):
    require(sys.platform == "win32", "native exact-path staging requires Windows")
    destinations = tuple(Path(plan["encoded_paths_by_file"][source.name]) for source in sources)
    for dest in destinations:
        require(dest.parent.resolve(strict=True) == dest.parent and dest.parent.is_dir() and not dest.parent.is_junction(),
                "native encoded directory is unavailable or redirected")
        require(not os.path.lexists(dest), f"encoded target already exists: {dest.name}")
    return destinations


def stage(plan, sources, destinations, result):
    require(all(not os.path.lexists(path) for path in destinations), "encoded target became occupied before staging")
    result["staged_filename_sha256"] = staged = {}
    for source, destination in zip(sources, destinations, strict=True):
        expected = plan["generated_files"][source.name]
        baseline.checked(source, expected["sha256"], owner=source.parent, size=expected["bytes"])
        with source.open("rb") as reader, destination.open("xb") as writer:
            copyfileobj(reader, writer)
        baseline.checked(destination, expected["sha256"], owner=destination.parent, size=expected["bytes"])
        staged[destination.name] = digest(destination)


def resolution(author, parent, assembly, child_path, scene):
    from ProbeAssemblyRebuild import model_state

    scene["parent_state"] = model_state(author, parent)
    components = author.get(assembly, "GetComponents", True) or ()
    scene["top_level_component_count"] = len(components)
    for raw in components[:2]:
        component = author.typed(raw, "Component2")
        row = {"name": str(author.get(component, "Name2"))}
        scene["occurrences"].append(row)
        row["component_path"] = str(author.get(component, "GetPathName"))
        row["suppression_state"] = int(author.get(component, "GetSuppression2"))
        row["reported_suppressed"] = bool(author.get(component, "IsSuppressed"))
        row["fixed"] = bool(author.get(component, "IsFixed"))
        row["referenced_configuration"] = str(author.get(component, "ReferencedConfiguration"))
        child = author.get(component, "GetModelDoc2")
        row["model_doc_available"] = child is not None
        row["loaded_model_path"] = None if child is None else str(author.get(child, "GetPathName"))
        row["matches_exact_child"] = row["model_doc_available"] and all(
            baseline.exact_file(path, child_path) for path in (row["component_path"], row["loaded_model_path"])
        )
        transform = author.typed(author.get(component, "Transform2"), "MathTransform")
        row["transform"] = [float(value) for value in author.get(transform, "ArrayData")]


def capture(recorder, label, author, parent, assembly, child, entry, row):
    snapshot = row[label + "_resolution"] = {"occurrences": []}
    try:
        recorder.call(f"log {label} component resolution", resolution, author, parent, assembly, child, snapshot)
    except Exception as error:
        snapshot["exception"] = repr(error)
    return baseline.capture(recorder, label, author, parent, assembly, child, entry, row)


def measure(packet, files, output, row):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    recorder = Recorder(output / "GeneratedCalls.json", {"lane": "Generated", "read_only": True, "path_mode": "exact_encoded"})
    controller = parent = None
    original = {path: digest(path) for path in files}
    entry = packet["generated"]
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = row["oracle_identity"] = recorder.call("verify pinned executable", application_identity, controller.app)
            require(identity["version_matches"] and identity["file_version"] == baseline.ORACLE_VERSION and identity["sha256"] == packet["oracle_sha256"]
                    and identity["process_id"] == controller.process_id and controller.revision == "34.5.2", "oracle build or ownership differs")
            author = CurveAuthor(controller.app, recorder, Swapp)
            parent, errors, warnings = recorder.call("open exact encoded assembly read-only", controller.open, files[0], read_only=True)
            row.update(opened=parent is not None, open_errors=errors, open_warnings=warnings, requested_path=str(files[0]),
                       file_not_found_bit=bool(errors & FILE_NOT_FOUND))
            require(parent is not None, "OpenDoc6 returned no encoded parent")
            row["returned_parent_path"] = str(author.get(parent, "GetPathName"))
            require(baseline.exact_file(row["returned_parent_path"], files[0]), "native parent path differs")
            assembly = author.typed(parent, "AssemblyDoc")
            try:
                row["first_pose"] = recorder.call("first occurrence transforms after open", baseline.first_pose, author, assembly, entry["case"])
            except Exception as error:
                row["first_pose"] = {"pose": "unobserved", "exception": repr(error)}
            initial = capture(recorder, "initial", author, parent, assembly, files[1], entry, row)
            row["forced_rebuild"] = bool(recorder.call("rebuild full assembly", author.get, parent, "ForceRebuild3", False))
            rebuilt = capture(recorder, "rebuilt", author, parent, assembly, files[1], entry, row)
            row["passed"] = errors == warnings == 0 and row["forced_rebuild"] and initial["matches"] and rebuilt["matches"]
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
    row["input_hashes_unchanged"] = all(path.is_file() and digest(path) == expected for path, expected in original.items())
    row["passed"] = bool(row["passed"] and row["input_hashes_unchanged"] and not row["dialogs"] and not row.get("controller_diagnostics")
                         and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"])
    recorder.data.update(result=row, passed=row["passed"], finished_at=time.time())
    recorder.flush()


def run(path, sha):
    plan, packet, control, frozen = verify(path, sha)
    output = path.parent / "Inspection"
    require(not output.exists() and not output.is_symlink(), "choose an unused exact-path output")
    output.mkdir()
    record = output / "DistanceMateResults.json"
    result = {
        "schema": SCHEMA, "path_plan_sha256": sha, "baseline_packet_sha256": BASE_PACKET, "baseline_native_result_sha256": BASE_RESULT,
        "writer_revision": packet["generated"]["writer_revision"], "oracle_sha256": packet["oracle_sha256"], "read_only": True,
        "heldout_inputs_tested": 0, "heldout_acceptance": False, "native_acceptance": False, "driving_edit_tested": False, "persistence_tested": False,
        "passed": False, "controls_healthy": False, "distinct_processes": 0, "phases": [], "started_at": time.time(),
    }
    try:
        paths = exclusive_targets(plan, frozen)
    except Exception as error:
        result.update(preflight_exception=repr(error), finished_at=time.time())
        write_json(record, result)
        return result

    def phase(label, files):
        row = {"label": label, "passed": False}
        result["phases"].append(row)
        write_json(record, result)
        if label == "Generated":
            measure(packet, files, output, row)
        else:
            baseline.measure(packet, packet["control"], files, output, row)
        write_json(record, result)
        return row

    candidate = {}
    try:
        if phase("ControlBefore", control)["passed"]:
            stage(plan, frozen, paths, result)
            candidate = phase("Generated", paths)
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        try:
            phase("ControlAfter", control)
        except Exception as error:
            result["control_after_exception"] = repr(error)
        result["controls_healthy"] = [row["passed"] for row in result["phases"] if row["label"].startswith("Control")] == [True, True]
        try:
            verify(path, sha)
            result["frozen_inputs_unchanged"] = True
        except Exception as error:
            result["frozen_inputs_unchanged"] = False
            result["final_verification_error"] = repr(error)
        result["staged_inputs_unchanged"] = all(path.is_file() and digest(path) == plan["generated_files"][path.name]["sha256"]
                                                for path in paths)
        identities = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in result["phases"]}
        result["distinct_processes"] = sum(type(value) is int and value > 0 for value in identities)
        result["passed"] = bool(result["controls_healthy"] and result["frozen_inputs_unchanged"] and result["staged_inputs_unchanged"]
                                and result["distinct_processes"] == 3
                                and candidate.get("passed") and "exception" not in result)
        result["finished_at"] = time.time()
        write_json(record, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Verify or run the bracketed distance trial at both exact encoded native paths")
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("plan", type=Path)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    path = args.plan.resolve(strict=True)
    if args.mode == "verify":
        verify(path, args.plan_sha256)
        print(json.dumps({"verified_exact_path_plan": args.plan_sha256}))
        return 0
    result = run(path, args.plan_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
