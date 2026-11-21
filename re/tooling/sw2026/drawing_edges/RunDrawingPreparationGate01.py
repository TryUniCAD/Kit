from __future__ import annotations

import argparse
from functools import partial
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools"))
import InspectDrawingEdgeQualification01 as baseline

sys.path.insert(0, str(Path(__file__).resolve().parent))

BASE_TRIAL = "2c2ac4aa9a09a170c9667abc8d81d6cf5c25a4f6192cf436ef7380f14869adf7"
BASE_RESULT = "92f51a9a5c5e7c7136b01d7a56d73c840e1a5e81df8f7af4a612ca36aa644401"
FAILED_TRACE = "040e859f432f6b0b3999a0e65b74706a4f7d5d9d385fe43a0f17e4196289c468"
TOOLS = {
    "DrawingSaveAggregateDbgEng.py",
    "DrawingSavePreviewGateDbgEng.py",
    "DrawingSavePropertiesGateDbgEng.py",
    "DrawingEdgeCacheTrace01.py",
    "ObserveDrawingEdgeCache01.py",
    "DrawingPreparationGateTrace01.py",
    "RunDrawingPreparationGate01.py",
}
ROLES = {"ControlBefore": False, "PreparationProbe": True, "ControlAfter": False}


def verify(path, expected):
    baseline.require(
        baseline.digest(path) == expected, "preparation probe manifest differs"
    )
    config = json.loads(path.read_bytes())
    root = path.parent.resolve(strict=True)
    baseline.require(
        Path(__file__).resolve().parent == root / "ProbeTools",
        "run the exact frozen probe closure",
    )
    baseline.require(
        config["schema"] == "kit.sw2026.drawing-preparation-gate.v1"
        and config["base_trial_sha256"] == BASE_TRIAL
        and config["heldout_inputs_read"] == 0
        and config["native_acceptance"] is False
        and set(config["probe_tools_sha256"]) == TOOLS,
        "unexpected preparation-gate scope",
    )
    for name, value in config["probe_tools_sha256"].items():
        baseline.checked(root, "ProbeTools/" + name, value)
    request = baseline.verify(root / "Trial.json", BASE_TRIAL)
    prior = json.loads(
        baseline.checked(root, "PassedBaseline.json", BASE_RESULT).read_bytes()
    )
    failed = json.loads(
        baseline.checked(root, "UnobservedTrace.json", FAILED_TRACE).read_bytes()
    )
    baseline.checked(root, "SourceRules.json", config["source_rules_sha256"])
    binding = json.loads(
        baseline.checked(
            root, "SourceViewBinding.json", config["source_view_binding_sha256"]
        ).read_bytes()
    )
    baseline.require(
        prior["passed"] is True
        and prior["controls_healthy"] is True
        and prior["distinct_processes"] == 6
        and failed["passed"] is False
        and failed["generated_skipped"]
        and len(failed["phases"]) == 2,
        "the distinct passing lifecycle and failed trace are required",
    )
    baseline.require(
        binding["drawing_sha256"] == request["cases"][0]["drawing_sha256"]
        and binding["model_view_class"] == "moAbsoluteView"
        and binding["native_view_id"] == config["model_view_native_id"]
        and type(binding["native_view_id"]) is int,
        "exact disclosed source-view identity differs",
    )
    baseline.require(
        config["rva"] == 0x347BCE
        and config["module_sha256"]
        == "61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47",
        "only the source-bound drawing decision is allowed",
    )
    return config, request


def worker(job):
    config, request = verify(Path(job["config"]), job["config_sha256"])
    role = job["role"]
    baseline.require(
        os.name == "nt" and role in ROLES,
        "the sole oracle owner runs exact disclosed roles",
    )
    case = request["cases"][0]
    root = Path(job["config"]).parent
    directory = root / "Inspection" / role
    source = root / case["drawing_source"]
    active = {}
    if ROLES[role]:
        import AuthorCurves as curves
        import Swapp
        import ObserveDrawingEdgeCache01 as observer
        from DrawingPreparationGateTrace01 import PreparationGateTrace, qualified

        original_author, original_save = curves.CurveAuthor, Swapp.Sw.save_as
        original_trace, original_evaluation = (
            observer.EdgeCacheTrace,
            observer.qualified,
        )

        class ProbeAuthor(original_author):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                active["author"] = self

        def observed_save(controller, model, target):
            author = active.get("author")
            baseline.require(
                author is not None and author.model is model,
                "preparation probe lost its actual document",
            )
            status, trace, evaluation = observer.save_with_edge_trace(
                controller,
                author,
                author.typed(model, "DrawingDoc"),
                target,
                Path(config["debugger_directory"]),
                save_operation=partial(original_save, controller),
            )
            active["trace"], active["evaluation"] = trace, evaluation
            return status

        curves.CurveAuthor, Swapp.Sw.save_as = ProbeAuthor, observed_save
        observer.EdgeCacheTrace = partial(
            PreparationGateTrace, expected_view_id=config["model_view_native_id"]
        )
        observer.qualified = qualified
        try:
            result = baseline.phase(
                root / "Trial.json",
                BASE_TRIAL,
                case,
                directory,
                source,
                case["drawing_sha256"],
                expected_tree=job.get("tree"),
            )
        finally:
            curves.CurveAuthor, Swapp.Sw.save_as = original_author, original_save
            observer.EdgeCacheTrace, observer.qualified = (
                original_trace,
                original_evaluation,
            )
        result["ordinary_annotation_save_passed"] = result["passed"]
        result["preparation_observer"] = active.get("trace") or {}
        result["preparation_evaluation"] = active.get("evaluation") or {}
        result["diagnostic_completed"] = bool(
            result["passed"]
            and result["preparation_evaluation"].get("observer_completed_cleanly")
        )
    else:
        result = baseline.phase(
            root / "Trial.json",
            BASE_TRIAL,
            case,
            directory,
            source,
            case["drawing_sha256"],
            expected_tree=job.get("tree"),
        )
        result["ordinary_annotation_save_passed"] = result["passed"]
        result["diagnostic_completed"] = result["passed"]
    result["cache_lookup_observed"] = False
    result["generated_native_inputs_run"] = 0
    result["native_acceptance"] = False
    baseline.write_json(directory / "Result.json", result)
    return result


def dispatch(path, expected, role, tree):
    directory = path.parent / "Inspection"
    job = {"config": str(path), "config_sha256": expected, "role": role, "tree": tree}
    job_path = directory / (role + ".job.json")
    baseline.write_json(job_path, job)
    try:
        process = subprocess.run(
            [
                sys.executable,
                "-B",
                str(Path(__file__).resolve()),
                "worker",
                str(job_path),
            ],
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
        )
        captured = {
            "exit_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as error:
        captured = {
            "exit_code": None,
            "stdout": str(error.stdout or ""),
            "stderr": str(error.stderr or ""),
            "timed_out": True,
        }
    baseline.write_json(directory / (role + ".transport.json"), captured)
    phase_path = directory / role / "Result.json"
    result = (
        json.loads(phase_path.read_bytes())
        if phase_path.is_file()
        else {"passed": False, "diagnostic_completed": False}
    )
    result.update(
        worker_exit_code=captured["exit_code"], worker_timed_out=captured["timed_out"]
    )
    result["diagnostic_completed"] = bool(
        result.get("diagnostic_completed")
        and captured["exit_code"] == 0
        and not captured["timed_out"]
    )
    return result


def run(path, expected):
    config, request = verify(path, expected)
    baseline.require(
        os.name == "nt", "only the root-owned Windows oracle runs the diagnostic"
    )
    output = path.parent / "Inspection"
    output.mkdir()
    result = {
        "schema": "kit.sw2026.drawing-preparation-gate-result.v1",
        "passed": False,
        "diagnostic_completed": False,
        "packet_sha256": expected,
        "phases": {},
        "native_acceptance": False,
        "cache_lookup_observed": False,
        "generated_native_inputs_run": 0,
        "heldout_inputs_read": 0,
    }
    phases = result["phases"]
    try:
        phases["ControlBefore"] = dispatch(path, expected, "ControlBefore", None)
        baseline.write_json(output / "Result.json", result)
        if phases["ControlBefore"].get("passed"):
            phases["PreparationProbe"] = dispatch(
                path,
                expected,
                "PreparationProbe",
                phases["ControlBefore"]["initial_state"]["drawing_tree"],
            )
    except Exception as error:
        result["error"] = repr(error)
    finally:
        try:
            phases["ControlAfter"] = dispatch(path, expected, "ControlAfter", None)
        except Exception as error:
            result["control_after_error"] = repr(error)
        result["controls_healthy"] = all(
            phases.get(role, {}).get("passed") is True
            for role in ("ControlBefore", "ControlAfter")
        )
        identities = [
            row.get("oracle_identity", {}).get("process_creation_filetime")
            for row in phases.values()
        ]
        result["distinct_processes"] = len(set(identities) - {None})
        result["inputs_unchanged"] = all(
            baseline.digest(path.parent / case[label + "_source"])
            == case[label + "_sha256"]
            for case in request["cases"]
            for label in ("drawing", "part")
        )
        probe = phases.get("PreparationProbe", {})
        result["preparation_gate_observed"] = (
            probe.get("preparation_evaluation", {}).get("preparation_gate_observed")
            is True
        )
        result["diagnostic_completed"] = bool(
            result["controls_healthy"]
            and result["inputs_unchanged"]
            and result["distinct_processes"] == 3
            and len(phases) == 3
            and all(row.get("diagnostic_completed") for row in phases.values())
        )
        result["passed"] = result["diagnostic_completed"]
        baseline.write_json(output / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "run", "worker"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--sha256")
    args = parser.parse_args()
    if args.command == "worker":
        result = worker(json.loads(args.path.read_bytes()))
        return 0 if result["diagnostic_completed"] else 3
    baseline.require(args.sha256 is not None, "the frozen diagnostic hash is required")
    path = args.path.resolve(strict=True)
    if args.command == "verify":
        verify(path, args.sha256)
        print(
            json.dumps(
                {"passed": True, "cad_processes_started": 0, "native_acceptance": False}
            )
        )
        return 0
    result = run(path, args.sha256)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "diagnostic_completed",
                    "controls_healthy",
                    "distinct_processes",
                    "preparation_gate_observed",
                    "native_acceptance",
                )
            }
        )
    )
    return 0 if result["diagnostic_completed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
