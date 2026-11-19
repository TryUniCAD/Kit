from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools"))
import InspectGeneratedConcentric as baseline

BASE_TRIAL = "5b90a632eab95d19fdf4f676798ec2bc44a6f0d464595a8198be25984d77ad34"
ROLES = ("ControlBefore", "StandaloneChild", "ParentRebuild", "ControlAfter")


def verify(path, expected):
    baseline.require(
        baseline.digest(path) == expected, "concentric open diagnostic changed"
    )
    config = json.loads(path.read_bytes())
    root = path.parent.resolve(strict=True)
    baseline.require(
        Path(__file__).resolve().parent == root / "DiagnosticTools"
        and config["schema"] == "kit.sw2026.concentric-open-diagnostic.v1"
        and config["base_trial_sha256"] == BASE_TRIAL
        and config["case"] == "Feature"
        and config["heldout_inputs_read"] == 0
        and config["native_acceptance"] is False,
        "unexpected diagnostic scope",
    )
    baseline.checked(
        root / "DiagnosticTools" / Path(__file__).name, config["inspector_sha256"]
    )
    baseline.checked(root / "NativeFailure.json", config["native_failure_sha256"])
    return config, baseline.verify(root / "Trial.json", BASE_TRIAL)


def model_state(author, model):
    extension = author.get(model, "Extension")
    configuration = author.get(model, "GetActiveConfiguration")
    return {
        "actual_path": str(author.get(model, "GetPathName")),
        "actual_document_type": int(author.get(model, "GetType")),
        "needs_rebuild": int(author.get(extension, "NeedsRebuild2")),
        "save_flag": bool(author.get(model, "GetSaveFlag")),
        "whats_wrong": int(author.get(extension, "GetWhatsWrongCount")),
        "update_stamp": int(author.get(model, "GetUpdateStamp")),
        "active_configuration": str(author.get(configuration, "Name")),
    }


def child_measurement(author, child, prediction):
    import Swapp
    from AuthorAssemblySources import feature_tree
    from ConcentricMateEvidence import configuration, local_cylinder

    expected = prediction["initial"]["child"]
    actual = Swapp.mass(child)
    baseline.require(actual is not None, "standalone cylinder geometry is unavailable")
    for name in ("volume", "area"):
        author.rec.close_number(
            "standalone child " + name, actual[name], expected[name], absolute=1e-15
        )
    for index in range(3):
        author.rec.close_number(
            "standalone child centroid " + str(index),
            actual["com"][index],
            expected["com"][index],
            absolute=1e-12,
        )
    _, cylinder = local_cylinder(author, child, prediction)
    dimensions = {}
    for name, value in (
        (prediction["radial_parameter"], prediction["radial_value_m"]),
        (prediction["depth_parameter"], prediction["depth_m"]),
    ):
        dimension = author.get(child, "Parameter", name)
        baseline.require(
            dimension is not None
            and int(author.get(dimension, "DrivenState")) == 2
            and not author.get(dimension, "ReadOnly"),
            "actual child driving dimension is unavailable",
        )
        dimensions[name] = float(author.get(dimension, "SystemValue"))
        author.rec.close_number(name, dimensions[name], value)
    tree = feature_tree(author, child)
    baseline.require(
        [[row["name"], row["type"], row["parent"]] for row in tree]
        == prediction["child_tree"]
        and all(
            row["error"] == 0 and row["warning"] is False and row["suppressed"] is False
            for row in tree
        ),
        "actual child tree or feature diagnostics differ",
    )
    return {
        "mass": actual,
        "cylinder": cylinder,
        "dimensions_m": dimensions,
        "tree": tree,
        "configuration": configuration(
            author, child, prediction["child_configuration"]
        ),
    }


def observe(author, model, role, child_path, prediction):
    result = {"document": model_state(author, model)}
    if role == "StandaloneChild":
        bodies = author.get(author.typed(model, "PartDoc"), "GetBodies2", 0, True) or ()
        result["visible_bodies"] = len(bodies)
        try:
            result["strict_child_geometry"] = child_measurement(
                author, model, prediction
            )
            result["strict_capture_passed"] = True
        except Exception as error:
            result["strict_capture_passed"] = False
            result["strict_capture_error"] = {
                "type": type(error).__name__,
                "error": str(error),
            }
        return result
    assembly = author.typed(model, "AssemblyDoc")
    values = author.get(assembly, "GetComponents", True) or ()
    result["direct_component_count"] = int(
        author.get(assembly, "GetComponentCount", True)
    )
    result["components"] = []
    for raw in values:
        component = author.typed(raw, "Component2")
        child = author.get(component, "GetModelDoc2")
        row = {
            "name": str(author.get(component, "Name2")),
            "native_id": int(author.get(component, "GetID")),
            "path": str(author.get(component, "GetPathName")),
            "configuration": str(author.get(component, "ReferencedConfiguration")),
            "fixed": bool(author.get(component, "IsFixed")),
            "suppressed": bool(author.get(component, "IsSuppressed")),
            "resolved_child_nonnull": child is not None,
        }
        if child is not None:
            row["child"] = model_state(author, child)
            row["visible_child_bodies"] = len(
                author.get(author.typed(child, "PartDoc"), "GetBodies2", 0, True) or ()
            )
        result["components"].append(row)
    try:
        result["strict_assembly_capture"], _ = baseline.capture(
            author, model, assembly, child_path, prediction
        )
        result["strict_capture_passed"] = True
    except Exception as error:
        result["strict_capture_passed"] = False
        result["strict_capture_error"] = {
            "type": type(error).__name__,
            "error": str(error),
        }
    return result


def phase(path, expected, role):
    baseline.require(
        os.name == "nt", "only the root-owned Windows oracle runs the diagnostic"
    )
    config, job = verify(path, expected)
    baseline.require(role in ROLES, "unknown diagnostic role")
    if role.startswith("Control"):
        result = baseline.phase(path.parent / "Trial.json", BASE_TRIAL, "Feature", role)
        result["diagnostic_completed"] = result["passed"]
        result["native_acceptance"] = False
        baseline.write_json(
            path.parent / "Inspection" / "Feature" / role / "DiagnosticResult.json",
            result,
        )
        return result
    runtime = job["guest_runtime"]
    baseline.require(
        tuple(sys.version_info[:3]) == tuple(map(int, runtime["version"].split(".")))
        and struct.calcsize("P") * 8 == runtime["pointer_bits"]
        and Path(sys.executable).samefile(runtime["executable"]),
        "the pinned guest runtime differs",
    )
    case = job["cases"]["Feature"]
    prediction = json.loads((path.parent / case["prediction_path"]).read_bytes())[
        "generated"
    ]
    child_path = baseline.input_path(case["inputs"]["generated_child"])
    source = (
        child_path
        if role == "StandaloneChild"
        else baseline.input_path(case["inputs"]["generated_parent"])
    )
    doc_type = 1 if role == "StandaloneChild" else 2
    directory = path.parent / "Inspection" / "Feature" / role
    directory.mkdir(parents=True, exist_ok=False)
    from AuthorCurves import CurveAuthor, Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    import Swapp

    recorder = Recorder(
        directory / "Record.json",
        {"case": "Feature", "role": role, "diagnostic_sha256": expected},
    )
    result = {
        "diagnostic_completed": False,
        "role": role,
        "native_acceptance": False,
        "file_saves": 0,
        "parameter_edits": 0,
    }
    controller = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle diagnostic oracle", Swapp.sweep)
            controller = recorder.call("start fresh diagnostic oracle", Swapp.Sw)
            identity = recorder.call(
                "verify exact diagnostic oracle", application_identity, controller.app
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
                result["document_count_before_open"] == 0, "diagnostic load is not cold"
            )
            result["actual_OpenDoc6_request"] = {
                "file_name": str(source),
                "document_type": doc_type,
                "options": Swapp.OPEN_SILENT | Swapp.OPEN_READONLY,
                "configuration": "",
                "error_and_warning_types": "VT_I4|VT_BYREF",
                "source": "exact frozen Swapp.open implementation",
            }
            model, errors, warnings = recorder.call(
                "open exact diagnostic file",
                controller.open,
                str(source),
                doc_type,
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
                "unexpected diagnostic open result",
            )
            actual_path = str(author.get(model, "GetPathName"))
            actual_type = int(author.get(model, "GetType"))
            result.update(
                actual_returned_path=actual_path,
                actual_returned_document_type=actual_type,
                actual_returned_path_matches=baseline.same_file(actual_path, source),
            )
            baseline.require(
                result["actual_returned_path_matches"] and actual_type == doc_type,
                "diagnostic opened a different file or type",
            )
            result["before_rebuild"] = observe(
                author, model, role, child_path, prediction
            )
            result["force_rebuild_return"] = bool(
                author.get(model, "ForceRebuild3", False)
            )
            result["after_rebuild"] = observe(
                author, model, role, child_path, prediction
            )
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
        result["immutable_inputs_unchanged"] = True
    except Exception as error:
        recorder.failure(error)
        result["immutable_inputs_unchanged"] = False
    result["diagnostic_completed"] = bool(
        result["diagnostic_completed"]
        and result["immutable_inputs_unchanged"]
        and not result["dialogs"]
        and not result.get("controller_diagnostics")
        and not recorder.data["cleanup_errors"]
    )
    result["numeric_checks"] = len(recorder.data["checks"])
    recorder.data.update(result=result, passed=False)
    recorder.flush()
    baseline.write_json(directory / "DiagnosticResult.json", result)
    return result


def summary(path, expected):
    verify(path, expected)
    rows = {}
    for role in ROLES:
        source = path.parent / "Inspection" / "Feature" / role / "DiagnosticResult.json"
        if source.is_file():
            rows[role] = json.loads(source.read_bytes())
    identities = [
        row.get("oracle_identity", {}).get("process_creation_filetime")
        for row in rows.values()
    ]
    healthy = all(
        rows.get(role, {}).get("passed") is True
        for role in ("ControlBefore", "ControlAfter")
    )
    result = {
        "schema": "kit.sw2026.concentric-open-diagnostic-result.v1",
        "diagnostic_completed": bool(
            len(rows) == 4
            and len(set(identities) - {None}) == 4
            and healthy
            and all(row.get("diagnostic_completed") for row in rows.values())
        ),
        "controls_healthy": healthy,
        "distinct_processes": len(set(identities) - {None}),
        "phases": rows,
        "native_acceptance": False,
        "file_saves": 0,
        "parameter_edits": 0,
        "heldout_inputs_read": 0,
    }
    baseline.write_json(path.parent / "DiagnosticResult.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "phase", "summary"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--role", choices=ROLES)
    args = parser.parse_args()
    path = args.path.resolve(strict=True)
    if args.command == "verify":
        verify(path, args.sha256)
        print(json.dumps({"passed": True, "native_processes_started": 0}))
        return 0
    result = (
        summary(path, args.sha256)
        if args.command == "summary"
        else phase(path, args.sha256, args.role)
    )
    print(
        json.dumps(
            {
                "diagnostic_completed": result["diagnostic_completed"],
                "native_acceptance": False,
            }
        )
    )
    return 0 if result["diagnostic_completed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
