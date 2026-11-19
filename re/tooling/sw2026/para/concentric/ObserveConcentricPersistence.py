import argparse
import json
import os
from pathlib import Path
import struct
import sys
import time

from ConcentricNativeContract import ORACLE, ROLES, checked, digest, require, signature, validate_prediction, write_json
from InspectGeneratedConcentric import capture, input_path, same_file


SCHEMA = "kit.sw2026.concentric-persistence.v1"


def verify(packet, expected):
    root = packet.resolve().parent
    job = json.loads(checked(packet, expected).read_bytes())
    require(
        Path(__file__).resolve().parent == root / "Tools"
        and job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
        and job["roles"] == list(ROLES) and job["heldout_inputs_read"] == 0
        and job["require_preference_18_true"] is True,
        "the exact disclosed persistence packet is required",
    )
    for relative, wanted in job["files_sha256"].items():
        checked(root / relative, wanted)
    require(set(job["working_names"]) == set(job["generated_sha256"]) == set(job["controls"]) == {"parent", "child"},
            "expected a complete parent plus child pair")
    for role, name in job["working_names"].items():
        require(Path(name).name == name and "/" not in name and "\\" not in name, "invalid owned basename")
        checked(root / "Frozen" / name, job["generated_sha256"][role])
        checked(input_path(job["controls"][role]), job["controls"][role]["sha256"])
    predictions = json.loads((root / "Evidence/Prediction.json").read_bytes())
    require(set(predictions) == {"generated", "control"}, "both independent predictions are mandatory")
    for value in predictions.values():
        validate_prediction(value)
    child_stem = Path(job["working_names"]["child"]).stem
    require([row["name"] for row in predictions["generated"]["occurrences"]] == [child_stem + "-1", child_stem + "-2"],
            "generated occurrence names must match their actual shared child basenames")
    return job, predictions


def phase_record(root, expected, role):
    path = root / "Inspection" / role / "Record.json"
    if not path.is_file():
        return None
    row = json.loads(path.read_bytes())
    require(row["job"] == {"phase": role, "packet_sha256": expected}, "unauthenticated phase record")
    return row.get("result", {"passed": False, "stage": row["stage"], "first_failure": row["first_failure"]})


def working_paths(root, job):
    owner = root / "Working"
    require(owner.resolve() == owner and owner.is_dir() and not owner.is_symlink(), "the owned final directory changed")
    return tuple(owner / job["working_names"][role] for role in ("parent", "child"))


def verify_working(root, job, prior=None):
    parent, child = working_paths(root, job)
    hashes = job["generated_sha256"] if prior is None else {
        "parent": prior["saved"]["parent"], "child": prior["saved"]["child"]["native_sha256"],
    }
    return checked(parent, hashes["parent"]), checked(child, hashes["child"])


def ensure_runtime(root):
    runtime = json.loads((root / "Evidence/GuestPython.json").read_bytes())
    require(os.name == "nt"
            and tuple(sys.version_info[:3]) == tuple(map(int, runtime["version"].split(".")))
            and struct.calcsize("P") * 8 == runtime["pointer_bits"]
            and Path(sys.executable).samefile(runtime["executable"]), "the pinned Windows guest Python is required")


def run_phase(packet, expected, role):
    root = packet.resolve().parent
    job, predictions = verify(packet, expected)
    ensure_runtime(root)
    control = role in {"ControlBefore", "ControlAfter"}
    editing = role == "Generated"
    reopened = role == "Reopen"
    prior = None
    if editing or reopened:
        predecessor = "ControlBefore" if editing else "Generated"
        prior = phase_record(root, expected, predecessor)
        require(prior and prior["passed"] is True, f"{predecessor} must pass first")
    if control:
        parent, child_path = (input_path(job["controls"][side]) for side in ("parent", "child"))
    else:
        parent, child_path = verify_working(root, job, prior if reopened else None)
    prediction = predictions["control" if control else "generated"]
    target = root / "Inspection" / role
    target.mkdir(parents=True, exist_ok=False)

    import Swapp
    from AuthorCurves import CurveAuthor, Recorder
    from InspectCombinedPlanarMates import native_save
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    recorder = Recorder(target / "Record.json", {"phase": role, "packet_sha256": expected})
    result = {"role": role, "passed": False, "started_at": time.time(), "parameter_edits": 0, "file_saves": 0}
    controller = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("require idle owned Windows oracle", Swapp.sweep)
            controller = recorder.call("start fresh SOLIDWORKS", Swapp.Sw)
            identity = recorder.call("verify exact SOLIDWORKS 2026 SP05.2", application_identity, controller.app)
            require(identity["sha256"] == ORACLE and identity["version_matches"]
                    and identity["file_version"] == "34.5.2.0604", "unexpected oracle build")
            result["oracle_identity"] = identity
            author = CurveAuthor(controller.app, recorder, Swapp)
            require(int(author.get(controller.app, "GetDocumentCount")) == 0, "the oracle is not cold")
            result["preference_18_before_open"] = bool(author.get(controller.app, "GetUserPreferenceToggle", 18))
            require(result["preference_18_before_open"], "ordinary update-component-names policy must already be true")
            model, errors, warnings = recorder.call("open exact linked pair", controller.open, parent, read_only=not editing)
            result.update(open_errors=errors, open_warnings=warnings)
            require(model is not None and errors == warnings == 0
                    and same_file(author.get(model, "GetPathName"), parent), "native open warned, failed or selected a different parent")
            assembly = author.typed(model, "AssemblyDoc")
            result["initial"], child = capture(author, model, assembly, child_path, prediction, reopened)
            result["child_stamp_on_open"] = int(author.get(child, "GetUpdateStamp"))
            if reopened:
                require(result["child_stamp_on_open"] == prior["saved"]["child"]["update_stamp"], "fresh open child stamp differs from the saved child")
            require(bool(author.get(model, "ForceRebuild3", False)), "native assembly rebuild failed")
            result["rebuilt"], child = capture(author, model, assembly, child_path, prediction, reopened)
            original_signature = signature(result["initial"])
            require(signature(result["rebuilt"]) == original_signature, "rebuild changed actual native identities")
            if editing:
                dimension = author.get(child, "Parameter", prediction["depth_parameter"])
                result["parameter_edits"] += 1
                status = int(author.get(dimension, "SetSystemValue3", prediction["edited_depth_m"], 1, Swapp.nothing()))
                result["depth_edit_status"] = status
                require(status == 0 and bool(author.get(child, "ForceRebuild3", False))
                        and bool(author.get(model, "ForceRebuild3", False)), "actual child depth edit or linked rebuild failed")
                result["edited"], _ = capture(author, model, assembly, child_path, prediction, True)
                require(signature(result["edited"]) == original_signature, "depth edit changed actual native identities")
                saved = native_save(author, model, assembly, parent, child_path, 2, recorder)
                result.update(saved=saved, file_saves=2)
                require(saved["parent"] != job["generated_sha256"]["parent"]
                        and saved["child"]["native_sha256"] != job["generated_sha256"]["child"], "paired save did not publish both updated archives")
                result["saved_state"], _ = capture(author, model, assembly, child_path, prediction, True)
                require(signature(result["saved_state"]) == original_signature, "paired save changed actual native identities")
            if reopened:
                require(original_signature == signature(prior["saved_state"]), "fresh reopen changed actual native identities")
            result["preference_18_after_observation"] = bool(author.get(controller.app, "GetUserPreferenceToggle", 18))
            require(result["preference_18_after_observation"], "the ordinary policy changed during the observation")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    try:
        verify(packet, expected)
        if reopened or (editing and "saved" in result):
            verify_working(root, job, prior if reopened else result)
        result["immutable_inputs_unchanged"] = True
    except Exception as error:
        recorder.failure(error, cleanup=True)
    result.update(dialogs=monitor.log, progress_windows=monitor.progress, finished_at=time.time(),
                  numeric_checks=len(recorder.data["checks"]), first_failure=recorder.data["first_failure"])
    result["passed"] = bool(result["passed"] and not result["first_failure"] and not result["dialogs"]
                            and not result.get("controller_diagnostics") and result.get("immutable_inputs_unchanged"))
    recorder.data.update(result=result, passed=result["passed"])
    recorder.flush()
    return result["passed"]


def summarize(packet, expected):
    verify(packet, expected)
    root = packet.resolve().parent
    phases = {role: phase_record(root, expected, role) for role in ROLES}
    controls_healthy = False
    births = []
    for value in phases.values():
        if value and "oracle_identity" in value:
            births.append(value["oracle_identity"]["process_creation_filetime"])
    complete = all(value and value["passed"] for value in phases.values())
    if complete:
        controls_healthy = signature(phases["ControlBefore"]["rebuilt"]) == signature(phases["ControlAfter"]["rebuilt"])
    passed = bool(complete and controls_healthy and len(births) == len(ROLES)
                  and all(first < second for first, second in zip(births, births[1:])))
    result = {"schema": SCHEMA, "packet_sha256": expected, "passed": passed,
              "controls_healthy": controls_healthy, "distinct_native_processes": len(set(births)),
              "numeric_checks": sum(value.get("numeric_checks", 0) for value in phases.values() if value),
              "heldout_acceptance": False, "phases": phases}
    write_json(root / "Result.json", result)
    return passed


def main():
    parser = argparse.ArgumentParser(description="Observe one disclosed concentric persistence packet")
    parser.add_argument("command", choices=("verify", "phase", "summary"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("sha256")
    parser.add_argument("role", choices=ROLES, nargs="?")
    args = parser.parse_args()
    if args.command == "phase":
        require(args.role is not None, "a phase role is required")
        passed = run_phase(args.packet, args.sha256, args.role)
    elif args.command == "summary":
        passed = summarize(args.packet, args.sha256)
    else:
        job, _ = verify(args.packet, args.sha256)
        verify_working(args.packet.resolve().parent, job)
        if os.name == "nt":
            ensure_runtime(args.packet.resolve().parent)
        passed = True
    print(json.dumps({"passed": passed, "role": args.role}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
