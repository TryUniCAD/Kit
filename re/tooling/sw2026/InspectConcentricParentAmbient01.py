import argparse
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
import InspectConcentricNames01 as name_probe
from InspectConcentricOpenDiagnostic01 import child_measurement, model_state

ROLES = ("ControlBefore", "ParentOff", "ParentOn", "ControlAfter")
BASE_TRIAL = "5b90a632eab95d19fdf4f676798ec2bc44a6f0d464595a8198be25984d77ad34"


def verify(path, expected):
    baseline.require(baseline.digest(path) == expected, "parent ambient trial changed")
    job = json.loads(path.read_bytes())
    baseline.require(
        path.parent.resolve() == ROOT
        and Path(__file__).resolve().parent == ROOT / "Tools"
        and job["schema"] == "kit.sw2026.concentric-parent-ambient-native.v1"
        and job["roles"] == list(ROLES)
        and job["heldout_inputs_read"]
        == job["file_saves"]
        == job["parameter_edits"]
        == 0
        and job["native_acceptance"] is False,
        "parent ambient scope differs",
    )
    for relative, digest in job["files_sha256"].items():
        baseline.checked(ROOT / relative, digest)
    baseline.verify(ROOT / "Baseline" / "Trial.json", BASE_TRIAL)
    generation = json.loads((ROOT / "Generation.json").read_bytes())
    baseline.require(
        generation["parents_byte_identical"] is True
        and generation["parent_stream_changes"] == []
        and generation["native_measured_children_exact"] is True
        and generation["source_names_retained_on_disk"] == ["Cylinder-1", "Cylinder-2"]
        and generation["variants"]["Off"]["linked_sdk"]["occurrences"]
        == generation["variants"]["On"]["linked_sdk"]["occurrences"]
        == job["occurrence_ids"],
        "generated pair ownership differs",
    )
    return job


def prediction(job, mode):
    base_job = json.loads((ROOT / "Baseline" / "Trial.json").read_bytes())
    value = json.loads(
        (
            ROOT / "Baseline" / base_job["cases"]["Feature"]["prediction_path"]
        ).read_bytes()
    )["generated"]
    geometry = json.loads((ROOT / "GeometryPrediction.json").read_bytes())
    baseline.require(
        value["initial"]["child"]
        == {key: geometry[key] for key in ("volume", "area", "com")}
        and geometry["bodies"] == 1,
        "frozen independent child geometry differs",
    )
    for key in (
        "depth_m",
        "depth_parameter",
        "radial_parameter",
        "radial_value_m",
        "radius_m",
        "child_configuration",
    ):
        baseline.require(value[key] == geometry[key], "child parameter differs: " + key)
    baseline.require(
        [row["name"] for row in value["occurrences"]] == ["Cylinder-1", "Cylinder-2"],
        "authored occurrence name expectations changed",
    )
    if mode == "On":
        rows = value["child_tree"]
        (environment,) = [row[0] for row in rows if row[1] == "EnvFolder"]
        retained = [
            row
            for row in rows
            if not (
                row[1] in {"AmbientLight", "DirectionLight"} and row[2] == environment
            )
        ]
        baseline.require(len(rows) - len(retained) == 4, "default light tree differs")
        (at,) = [index for index, row in enumerate(retained) if row[1] == "EnvFolder"]
        retained.insert(at + 1, [job["ambient_name"], "AmbientLight", environment])
        value["child_tree"] = retained
    return value


def attempt(action):
    try:
        return {"passed": True, "value": action()}
    except Exception as error:
        return {
            "passed": False,
            "error": {"type": type(error).__name__, "error": str(error)},
        }


def observe(author, model, child_path, expected, ids):
    import Swapp
    from AuthorAssemblySources import feature_tree, transform_matches
    from ConcentricMateEvidence import configuration, mate_state

    result = {"document": model_state(author, model)}
    author.rec.data.setdefault("parent_observations", []).append(result)
    author.rec.flush()
    result["reference_names"] = name_probe.names(author, model, child_path)
    assembly = author.typed(model, "AssemblyDoc")
    raw = author.get(assembly, "GetComponents", True) or ()
    baseline.require(
        len(raw)
        == int(author.get(assembly, "GetComponentCount", True))
        == int(author.get(assembly, "GetComponentCount", False))
        == len(ids)
        == 2,
        "expected two real direct occurrences",
    )
    objects = {}
    for value in raw:
        component = author.typed(value, "Component2")
        native_id = int(author.get(component, "GetID"))
        baseline.require(
            native_id in ids and native_id not in objects,
            "foreign or duplicate occurrence ID",
        )
        objects[native_id] = component
    components = [objects[value] for value in ids]
    child = author.get(components[0], "GetModelDoc2")
    baseline.require(
        child is not None
        and baseline.same_file(author.get(child, "GetPathName"), child_path),
        "actual intended child is unavailable",
    )
    result["child_document"] = model_state(author, child)
    result["configurations"] = [
        configuration(author, model, expected["parent_configuration"]),
        configuration(author, child, expected["child_configuration"]),
    ]
    rows = []
    result["occurrences"] = rows
    for index, component in enumerate(components):
        loaded = author.get(component, "GetModelDoc2")
        row = {
            "name": str(author.get(component, "Name2")),
            "authored_name": expected["occurrences"][index]["name"],
            "native_id": int(author.get(component, "GetID")),
            "path": str(author.get(component, "GetPathName")),
            "configuration": str(author.get(component, "ReferencedConfiguration")),
            "fixed": bool(author.get(component, "IsFixed")),
            "hidden": bool(author.get(component, "IsHidden", False)),
            "suppressed": bool(author.get(component, "IsSuppressed")),
            "transform": [
                float(value)
                for value in author.get(
                    author.typed(author.get(component, "Transform2"), "MathTransform"),
                    "ArrayData",
                )
            ],
        }
        row["actual_child_path_matches"] = bool(
            loaded is not None
            and baseline.same_file(row["path"], child_path)
            and baseline.same_file(author.get(loaded, "GetPathName"), child_path)
        )
        row["visible_child_bodies"] = (
            len(
                author.get(author.typed(loaded, "PartDoc"), "GetBodies2", 0, True) or ()
            )
            if loaded is not None
            else 0
        )
        row["requested_transform_matches"] = transform_matches(
            row["transform"], expected["occurrences"][index]["transform"]
        )
        row["authored_name_matches"] = row["name"] == row["authored_name"]
        rows.append(row)
        baseline.require(
            row["actual_child_path_matches"]
            and row["configuration"] == expected["child_configuration"]
            and row["fixed"] == (index == expected["fixed_index"])
            and not row["hidden"]
            and not row["suppressed"]
            and row["visible_child_bodies"] == 1,
            "actual occurrence path/configuration/fixed state/body differs",
        )
    result["body_count"] = sum(row["visible_child_bodies"] for row in rows)
    result["strict_original_capture"] = attempt(
        lambda: name_probe.CAPTURE(author, model, assembly, child_path, expected)[0]
    )
    result["independent_child_geometry"] = attempt(
        lambda: child_measurement(author, child, expected)
    )

    def measure_parent():
        actual = author.rec.call(
            "measure actual parent geometry independent of names", Swapp.mass, model
        )
        baseline.require(actual is not None, "parent geometry is unavailable")
        wanted = expected["initial"]["assembly"]
        for key in ("volume", "area"):
            author.rec.close_number(
                "independent parent " + key, actual[key], wanted[key], absolute=1e-15
            )
        for index in range(3):
            author.rec.close_number(
                "independent parent centroid " + str(index),
                actual["com"][index],
                wanted["com"][index],
                absolute=1e-12,
            )
        return actual

    result["independent_parent_geometry"] = attempt(measure_parent)
    result["actual_parent_tree"] = attempt(lambda: feature_tree(author, model))
    mate_case = {
        "mate_name": expected["mate_name"],
        "radius_m": expected["radius_m"],
        "center_m": expected["center_m"],
        "lock_rotation": expected["rotation_locked"],
        "api_alignment": expected["api_alignment"],
    }
    result["actual_mate"] = attempt(
        lambda: mate_state(author, model, assembly, child, components, rows, mate_case)
    )
    result["independent_checks_passed"] = bool(
        result["reference_names"]["observation_complete"]
        and all(row["requested_transform_matches"] for row in rows)
        and all(
            result[key]["passed"]
            for key in (
                "independent_child_geometry",
                "independent_parent_geometry",
                "actual_parent_tree",
                "actual_mate",
            )
        )
        and result["document"]["whats_wrong"]
        == result["child_document"]["whats_wrong"]
        == 0
    )
    author.rec.flush()
    return result


def materialize(job, mode):
    working = Path(job["working_parent_guest_path"])
    child = Path(job["working_child_guest_path"])
    baseline.require(
        working.parent == child.parent and working.parent.name == "Working",
        "shared encoded working locator differs",
    )
    working.parent.mkdir(parents=True, exist_ok=True)
    for kind, path in (("parent", working), ("child", child)):
        source = ROOT / job["variants"][mode][kind]["file"]
        baseline.require(source.name == path.name, "working filename differs")
        if path.exists():
            baseline.require(
                baseline.digest(path)
                in {row[kind]["sha256"] for row in job["variants"].values()},
                "foreign working file cannot be replaced",
            )
        copyfile(source, path)
        baseline.checked(path, job["variants"][mode][kind]["sha256"])
    return working, child


def phase(path, expected, role):
    baseline.require(
        os.name == "nt" and role in ROLES, "only root runs the owned Windows phase"
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
    before = json.loads(
        (ROOT / "Inspection" / "ControlBefore" / "Result.json").read_bytes()
    )
    baseline.require(
        before["control"]["passed"] is True, "leading control has not passed"
    )
    runtime = job["guest_runtime"]
    baseline.require(
        tuple(sys.version_info[:3]) == tuple(map(int, runtime["version"].split(".")))
        and struct.calcsize("P") * 8 == runtime["pointer_bits"]
        and Path(sys.executable).samefile(runtime["executable"]),
        "pinned guest runtime differs",
    )
    mode = role.removeprefix("Parent")
    expected_state = prediction(job, mode)
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
    working = child = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle parent ambient oracle", Swapp.sweep)
            working, child = materialize(job, mode)
            controller = recorder.call("start fresh parent ambient oracle", Swapp.Sw)
            identity = recorder.call(
                "verify exact parent ambient oracle",
                application_identity,
                controller.app,
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
                "parent comparison is not cold",
            )
            result["actual_OpenDoc6_request"] = {
                "file_name": str(working),
                "document_type": 2,
                "options": Swapp.OPEN_SILENT | Swapp.OPEN_READONLY,
                "configuration": "",
                "status_domain": "VT_I4|VT_BYREF",
            }
            model, errors, warnings = recorder.call(
                "cold open same-locator parent ambient pair",
                controller.open,
                str(working),
                2,
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
                "unexpected parent diagnostic load status",
            )
            state = model_state(author, model)
            baseline.require(
                state["actual_document_type"] == 2
                and baseline.same_file(state["actual_path"], working),
                "parent comparison opened a foreign file",
            )
            result["before_rebuild"] = observe(
                author, model, child, expected_state, job["occurrence_ids"]
            )
            result["force_rebuild_return"] = bool(
                author.get(model, "ForceRebuild3", False)
            )
            result["after_rebuild"] = observe(
                author, model, child, expected_state, job["occurrence_ids"]
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
        for kind, current in (("parent", working), ("child", child)):
            baseline.require(current is not None, "working pair was not materialized")
            baseline.checked(current, job["variants"][mode][kind]["sha256"])
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
    result["independent_checks_passed"] = bool(
        result["diagnostic_completed"]
        and result.get("force_rebuild_return")
        and all(
            result[key]["independent_checks_passed"]
            for key in ("before_rebuild", "after_rebuild")
        )
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
    } - {None}
    healthy = all(
        rows.get(role, {}).get("control", {}).get("passed") is True
        for role in ("ControlBefore", "ControlAfter")
    )
    completed = bool(
        len(rows) == len(identities) == 4
        and healthy
        and all(row.get("diagnostic_completed") for row in rows.values())
    )
    independent = bool(
        completed
        and all(
            rows[role].get("independent_checks_passed")
            for role in ("ParentOff", "ParentOn")
        )
    )
    result = {
        "schema": "kit.sw2026.concentric-parent-ambient-result.v1",
        "diagnostic_completed": completed,
        "controls_healthy": healthy,
        "distinct_processes": len(identities),
        "phases": rows,
        "independent_geometry_and_mate_checks_passed": independent,
        "warning_changed_32_to_0": bool(
            completed
            and rows["ParentOff"]["open_warnings"] == 32
            and rows["ParentOn"]["open_warnings"] == 0
        ),
        "native_acceptance": False,
        "heldout_inputs_read": 0,
        "file_saves": 0,
        "parameter_edits": 0,
        "global_preference_changes": 0,
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
        for mode in ("Off", "On"):
            prediction(job, mode)
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
