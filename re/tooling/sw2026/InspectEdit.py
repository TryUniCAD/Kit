from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import Swapp
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity


def edit(source, destination, parameter_name, value, result, checkpoint):
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError("edited output requires a new destination distinct from its copied input")
    if source.suffix.casefold() != ".sldprt" or destination.suffix.casefold() != ".sldprt":
        raise ValueError("the depth-edit inspection requires explicit native part paths")
    if not math.isfinite(value) or value <= 0:
        raise ValueError("the edited depth must be a finite positive SI value")
    result.update(path=str(source), destination=str(destination), parameter=parameter_name, requested_value_m=value, stages=[])

    def mark(stage):
        result["stage"] = stage
        result["stages"].append({"stage": stage, "time": time.time()})
        checkpoint()

    with Swapp.Dismisser() as dismisser:
        controller = None
        model = None
        try:
            mark("oracle_idle_guard")
            Swapp.sweep()
            controller = Swapp.Sw()
            result["oracle_identity"] = application_identity(controller.app)
            if not result["oracle_identity"]["version_matches"]:
                raise RuntimeError("dimension edit requires the exact selected 2026 oracle build")
            mark("open_start")
            model, errors, warnings = controller.open(source)
            result.update(opened=model is not None, open_errors=errors, open_warnings=warnings)
            mark("open_return")
            if model is None:
                raise RuntimeError("native edit input did not open")
            mark("parameter_lookup_start")
            dimension = model.Parameter(parameter_name)
            if dimension is None:
                raise RuntimeError("the selected editable parameter is absent")
            result["original_value_m"] = float(dimension.SystemValue)
            mark("parameter_write_start")
            dimension.SystemValue = value
            result["readback_value_m"] = float(dimension.SystemValue)
            mark("parameter_write_return")
            mark("rebuild_start")
            result["rebuilt"] = bool(model.ForceRebuild3(False))
            mark("rebuild_return")
            for name, operation in (
                ("bodies", lambda: Swapp.bodies(model)),
                ("mass", lambda: Swapp.mass(model)),
                ("features", lambda: Swapp.features(model)),
                ("whats_wrong", lambda: Swapp.rebuild_errors(model)),
            ):
                mark(name + "_start")
                result[name] = operation()
                mark(name + "_return")
            mark("save_start")
            saved, errors, warnings = controller.save_as(model, destination)
            result.update(saved=saved, save_errors=errors, save_warnings=warnings)
            mark("save_return")
            if not saved or errors or warnings or not destination.is_file():
                raise RuntimeError("edited native copy did not save cleanly")
            result["edited_copy_sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
        except Exception as error:
            result.update(exception=repr(error), failure_stage=result.get("stage", "oracle_setup"))
        finally:
            if controller is not None:
                if model is not None:
                    controller.close_doc(model)
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = dismisser.log
    result["progress_windows"] = dismisser.progress
    checkpoint()


def metrics_match(row, expected):
    measured = row.get("mass", {})
    if row.get("bodies") != expected["bodies"]:
        return False
    actual_center = measured.get("com", ())
    if len(actual_center) != 3 or len(expected["com"]) != 3:
        return False
    pairs = [(measured.get(name), expected[name], 0.0) for name in ("volume", "area")]
    pairs.extend((actual, target, 1e-15) for actual, target in zip(actual_center, expected["com"], strict=True))
    return all(actual is not None and math.isfinite(actual) and math.isfinite(target) and math.isclose(actual, target, rel_tol=5e-7, abs_tol=absolute) for actual, target, absolute in pairs)


def main():
    job_path = Path(sys.argv[1])
    job = json.loads(job_path.read_text(encoding="utf-8"))
    output = Path(sys.argv[2])
    result = {"authority": "clean-vendor-dimension-edit-and-reopen", "instrumented": False, "started_at": time.time(), "generator": job.get("generator"), "job_sha256": hashlib.sha256(job_path.read_bytes()).hexdigest(), "inspector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "control_before": {}, "cases": [], "control_after": {}}

    def checkpoint():
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    inspect(job["control"], result=result["control_before"], checkpoint=checkpoint)
    for case in job["cases"]:
        source, destination = Path(case["source"]), Path(case["destination"])
        entry = {"name": case["name"], "source_sha256_before": hashlib.sha256(source.read_bytes()).hexdigest(), "expected": case["expected"], "baseline": {}, "edit": {}, "reopened": {}}
        result["cases"].append(entry)
        inspect(source, result=entry["baseline"], checkpoint=checkpoint)
        if healthy(entry["baseline"]):
            edit(source, destination, case["parameter"], case["value_m"], entry["edit"], checkpoint)
            if entry["edit"].get("saved") and not entry["edit"].get("exception"):
                inspect(destination, result=entry["reopened"], checkpoint=checkpoint)
        entry["source_sha256_after"] = hashlib.sha256(source.read_bytes()).hexdigest()
        entry["unchanged_source"] = entry["source_sha256_before"] == entry["source_sha256_after"]
        entry["baseline_match"] = healthy(entry["baseline"]) and metrics_match(entry["baseline"], case["expected"]["before"])
        entry["edit_match"] = healthy(entry["edit"]) and metrics_match(entry["edit"], case["expected"]["after"]) and entry["edit"].get("readback_value_m") == case["value_m"]
        entry["reopen_match"] = healthy(entry["reopened"]) and metrics_match(entry["reopened"], case["expected"]["after"])
        checkpoint()
    inspect(job["control"], result=result["control_after"], checkpoint=checkpoint)
    result["controls_healthy"] = healthy(result["control_before"]) and healthy(result["control_after"])
    result["geometry_edit_reopen_passed"] = bool(result["cases"]) and result["controls_healthy"] and all(case["unchanged_source"] and case["baseline_match"] and case["edit_match"] and case["reopen_match"] for case in result["cases"])
    result["finished_at"] = time.time()
    result["acceptance_limit"] = "polygon blind-extrusion geometry and one depth edit only; broader feature and source conversion acceptance remains unfinished"
    checkpoint()
    return int(not result["geometry_edit_reopen_passed"])


if __name__ == "__main__":
    raise SystemExit(main())
