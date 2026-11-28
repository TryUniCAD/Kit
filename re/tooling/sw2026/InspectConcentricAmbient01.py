import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from shutil import copyfile
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [
    str(ROOT / "Baseline" / "Tools"),
    str(ROOT / "Baseline" / "DiagnosticTools"),
]
import InspectGeneratedConcentric as baseline
from InspectConcentricOpenDiagnostic01 import child_measurement, model_state

ROLES = ("ControlBefore", "Off", "On", "ControlAfter")
BASE_TRIAL = "5b90a632eab95d19fdf4f676798ec2bc44a6f0d464595a8198be25984d77ad34"


def verify(path, expected):
    baseline.require(baseline.digest(path) == expected, "ambient trial changed")
    job = json.loads(path.read_bytes())
    baseline.require(
        path.parent.resolve() == ROOT
        and Path(__file__).resolve().parent == ROOT / "Tools"
        and job["schema"] == "kit.sw2026.concentric-ambient-native.v1"
        and job["heldout_inputs_read"]
        == job["file_saves"]
        == job["parameter_edits"]
        == 0
        and job["native_acceptance"] is False,
        "ambient trial scope differs",
    )
    for relative, digest in job["files_sha256"].items():
        baseline.checked(ROOT / relative, digest)
    baseline.verify(ROOT / "Baseline" / "Trial.json", BASE_TRIAL)
    return job


def prediction(job, role):
    base_job = json.loads((ROOT / "Baseline" / "Trial.json").read_bytes())
    value = json.loads(
        (
            ROOT / "Baseline" / base_job["cases"]["Feature"]["prediction_path"]
        ).read_bytes()
    )["generated"]
    geometry = json.loads((ROOT / "GeometryPrediction.json").read_bytes())
    baseline.require(
        value["initial"]["child"]
        == {key: geometry[key] for key in ("volume", "area", "com")},
        "independent geometry differs from the frozen source intent",
    )
    baseline.require(
        geometry["bodies"] == 1, "expected one independently predicted body"
    )
    for key in (
        "depth_m",
        "depth_parameter",
        "radial_parameter",
        "radial_value_m",
        "radius_m",
        "child_configuration",
    ):
        baseline.require(
            value[key] == geometry[key], "independent child parameter differs: " + key
        )
    if role == "On":
        rows = value["child_tree"]
        (environment,) = [row[0] for row in rows if row[1] == "EnvFolder"]
        light_kinds = {"AmbientLight", "DirectionLight"}
        retained = [
            row for row in rows if not (row[1] in light_kinds and row[2] == environment)
        ]
        baseline.require(
            len(rows) - len(retained) == 4, "frozen default environment shape differs"
        )
        (at,) = [index for index, row in enumerate(retained) if row[1] == "EnvFolder"]
        retained.insert(at + 1, [job["ambient_name"], "AmbientLight", environment])
        value["child_tree"] = retained
    return value


def phase(path, expected, role):
    baseline.require(
        os.name == "nt" and role in ROLES,
        "only root runs the owned Windows ambient phase",
    )
    job = verify(path, expected)
    directory = ROOT / "Inspection" / role
    directory.mkdir(parents=True, exist_ok=False)
    if role.startswith("Control"):
        row = baseline.phase(
            ROOT / "Baseline" / "Trial.json", BASE_TRIAL, "Feature", role
        )
        result = {
            "role": role,
            "diagnostic_completed": row["passed"],
            "control": row,
            "oracle_identity": row.get("oracle_identity"),
            "numeric_checks": row.get("numeric_checks", 0),
            "native_acceptance": False,
        }
        baseline.write_json(directory / "Result.json", result)
        return result
    runtime = job["guest_runtime"]
    baseline.require(
        tuple(sys.version_info[:3]) == tuple(map(int, runtime["version"].split(".")))
        and struct.calcsize("P") * 8 == runtime["pointer_bits"]
        and Path(sys.executable).samefile(runtime["executable"]),
        "pinned guest runtime differs",
    )
    source = ROOT / job["variants"][role]["file"]
    working = Path(job["working_child_guest_path"])
    baseline.require(
        working.name == source.name and working.parent.name == "Working",
        "working child locator differs",
    )
    working.parent.mkdir(parents=True, exist_ok=True)
    if working.exists():
        baseline.require(
            baseline.digest(working)
            in {row["sha256"] for row in job["variants"].values()},
            "foreign working child cannot be replaced",
        )
    copyfile(source, working)
    baseline.checked(working, job["variants"][role]["sha256"])
    expected_child = prediction(job, role)
    from AuthorCurves import CurveAuthor, Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    import Swapp

    recorder = Recorder(
        directory / "Record.json", {"role": role, "trial_sha256": expected}
    )
    result = {
        "role": role,
        "diagnostic_completed": False,
        "native_acceptance": False,
        "file_saves": 0,
        "parameter_edits": 0,
    }
    controller = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle ambient oracle", Swapp.sweep)
            controller = recorder.call("start fresh ambient oracle", Swapp.Sw)
            identity = recorder.call(
                "verify exact ambient oracle", application_identity, controller.app
            )
            baseline.require(
                identity["sha256"] == baseline.ORACLE
                and identity["version_matches"]
                and identity["file_version"] == "34.5.2.0604",
                "unexpected native oracle",
            )
            result["oracle_identity"] = identity
            author = CurveAuthor(controller.app, recorder, Swapp)
            result["document_count_before_open"] = int(
                author.get(controller.app, "GetDocumentCount")
            )
            baseline.require(
                result["document_count_before_open"] == 0,
                "ambient observation is not cold",
            )
            result["actual_OpenDoc6_request"] = {
                "file_name": str(working),
                "document_type": 1,
                "options": Swapp.OPEN_SILENT | Swapp.OPEN_READONLY,
                "configuration": "",
                "status_domain": "VT_I4|VT_BYREF",
            }
            model, errors, warnings = recorder.call(
                "cold open exact same-locator cylinder",
                controller.open,
                str(working),
                1,
                read_only=True,
            )
            result.update(
                returned_model_nonnull=model is not None,
                open_errors=errors,
                open_warnings=warnings,
                original_zero_warning_gate_passed=model is not None
                and errors == warnings == 0,
            )
            baseline.require(
                model is not None and errors == 0 and warnings in (0, 32),
                "unexpected ambient diagnostic load status",
            )
            result["initial_state"] = model_state(author, model)
            baseline.require(
                result["initial_state"]["actual_document_type"] == 1
                and baseline.same_file(result["initial_state"]["actual_path"], working),
                "ambient opened a foreign file or kind",
            )
            result["initial"] = child_measurement(author, model, expected_child)
            result["force_rebuild_return"] = bool(
                author.get(model, "ForceRebuild3", False)
            )
            baseline.require(
                result["force_rebuild_return"], "ambient child rebuild failed"
            )
            result["rebuilt_state"] = model_state(author, model)
            result["rebuilt"] = child_measurement(author, model, expected_child)
            result["diagnostic_completed"] = True
        except Exception as error:
            recorder.failure(error)
            result["error"] = {"type": type(error).__name__, "error": str(error)}
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    result.update(dialogs=monitor.log, progress_windows=monitor.progress)
    try:
        verify(path, expected)
        baseline.checked(working, job["variants"][role]["sha256"])
        result["immutable_inputs_unchanged"] = True
    except Exception as error:
        recorder.failure(error)
        result["immutable_inputs_unchanged"] = False
    result["numeric_checks"] = len(recorder.data["checks"])
    result["diagnostic_completed"] = bool(
        result["diagnostic_completed"]
        and result["immutable_inputs_unchanged"]
        and not result["dialogs"]
        and not result.get("controller_diagnostics")
        and not recorder.data["cleanup_errors"]
        and recorder.data["first_failure"] is None
    )
    recorder.data.update(result=result, passed=False)
    recorder.flush()
    baseline.write_json(directory / "Result.json", result)
    return result


def summary(path, expected):
    verify(path, expected)
    rows = {}
    for role in ROLES:
        source = ROOT / "Inspection" / role / "Result.json"
        if source.is_file():
            rows[role] = json.loads(source.read_bytes())
    identities = {
        (row.get("oracle_identity") or {}).get("process_creation_filetime")
        for row in rows.values()
    }
    identities.discard(None)
    healthy = all(
        rows.get(role, {}).get("control", {}).get("passed") is True
        for role in ("ControlBefore", "ControlAfter")
    )
    complete = (
        len(rows) == 4
        and len(identities) == 4
        and healthy
        and all(row.get("diagnostic_completed") for row in rows.values())
    )
    result = {
        "schema": "kit.sw2026.concentric-ambient-native-result.v1",
        "diagnostic_completed": complete,
        "controls_healthy": healthy,
        "distinct_processes": len(identities),
        "phases": rows,
        "warning_changed_32_to_0": bool(
            complete
            and rows["Off"]["open_warnings"] == 32
            and rows["On"]["open_warnings"] == 0
        ),
        "native_acceptance": False,
        "heldout_inputs_read": 0,
        "file_saves": 0,
        "parameter_edits": 0,
    }
    baseline.write_json(ROOT / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "phase", "summary"))
    parser.add_argument("trial", type=Path)
    parser.add_argument("--trial-sha256", required=True)
    parser.add_argument("--phase", choices=ROLES)
    args = parser.parse_args()
    path = args.trial.resolve(strict=True)
    if args.command == "verify":
        job = verify(path, args.trial_sha256)
        for role in ("Off", "On"):
            prediction(job, role)
        print(
            json.dumps(
                {
                    "verified": True,
                    "native_processes_started": 0,
                    "heldout_inputs_read": 0,
                }
            )
        )
        return 0
    result = (
        phase(path, args.trial_sha256, args.phase)
        if args.command == "phase"
        else summary(path, args.trial_sha256)
    )
    print(
        json.dumps(
            {
                "diagnostic_completed": result["diagnostic_completed"],
                "native_acceptance": False,
            }
        )
    )
    return 0 if result["diagnostic_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
