from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from AuthorAssemblySources import snapshot
from InspectCircleSketch import digest
from InspectFresh import healthy, inspect
from ObserveAssemblyLoad import AssemblyLoadMonitor
from OracleIdentity import application_identity


def state(author, model, assembly, label):
    result = snapshot(author, model, assembly, [], None, None, label)
    configuration = author.get(author.get(model, "ConfigurationManager"), "ActiveConfiguration")
    result["active_configuration"] = str(author.get(configuration, "Name"))
    result["configurations"] = list(author.get(model, "GetConfigurationNames") or ())
    result["needs_rebuild"] = int(author.get(author.get(model, "Extension"), "NeedsRebuild2"))
    return result


def inspect_assembly(*, path, expected_sha, directory, oracle_sha, save_copy):
    directory.mkdir()
    recorder = AuthorCurves.Recorder(directory / "Record.json", {"input": path.name, "sha256": expected_sha})
    result = {"input": path.name, "sha256": expected_sha, "passed": False, "opened": False}
    controller = model = None
    with AssemblyLoadMonitor() as dialogs:
        try:
            AuthorCurves.require(digest(path) == expected_sha, "assembly input differs from its published hash")
            recorder.call("require idle oracle", Swapp.sweep)
            controller = recorder.call("start fresh owned oracle", Swapp.Sw)
            identity = recorder.call("check pinned oracle build", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == oracle_sha and controller.revision == "34.5.2", "assembly oracle build differs")
            result["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = recorder.call("open empty assembly", controller.open, path, read_only=not save_copy)
            result.update(opened=model is not None, open_errors=errors, open_warnings=warnings)
            AuthorCurves.require(model is not None and errors == warnings == 0, "empty assembly open failed or warned")
            assembly = author.typed(model, "AssemblyDoc")
            result["initial"] = recorder.call("measure initial assembly", state, author, model, assembly, "initial")
            result["rebuild_return"] = bool(author.get(model, "ForceRebuild3", False))
            AuthorCurves.require(result["rebuild_return"], "empty assembly rebuild failed")
            result["rebuilt"] = recorder.call("measure rebuilt assembly", state, author, model, assembly, "rebuilt")
            if save_copy:
                saved = directory / "NativeSaved.SLDASM"
                status = recorder.call("save a separate native copy", controller.save_as, model, saved)
                result["save_status"] = list(status)
                AuthorCurves.require(status == (True, 0, 0), "empty assembly save failed or warned")
                result["saved"] = recorder.call("measure saved assembly", state, author, model, assembly, "saved")
                result.update(saved_path=str(saved), saved_sha256=digest(saved), saved_bytes=saved.stat().st_size)
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if model is not None:
                recorder.call("close owned assembly document", controller.close_doc, model)
            if controller is not None:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result.update(input_immutable=digest(path) == expected_sha, dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["passed"] = bool(result["passed"] and result["input_immutable"] and not result["dialogs"] and not result.get("controller_diagnostics"))
    recorder.data.update(result=result, finished_at=time.time())
    recorder.flush()
    result["record_sha256"] = digest(directory / "Record.json")
    return result


def main():
    job_path = Path(sys.argv[1]).resolve()
    job = json.loads(job_path.read_bytes())
    AuthorCurves.require(job["schema"] == "kit.sw2026.empty-assembly-candidate-job.v1", "unexpected empty assembly candidate job")
    checkout, output, control, native = (Path(job[name]).resolve() for name in ("checkout_root", "output", "control", "native_empty"))
    AuthorCurves.require(output.is_absolute() and not output.is_relative_to(checkout), "oracle output must be outside the checkout")
    AuthorCurves.require(native.name == "A12SyncedEmpty.SLDASM", "native input must be the previously disclosed empty discovery control")
    AuthorCurves.require(digest(control) == job["control_sha256"] and digest(native) == job["native_empty_sha256"], "oracle controls differ from the frozen inputs")
    candidates = [(row["name"], Path(row["path"]).resolve(), row["sha256"]) for row in job["candidates"]]
    AuthorCurves.require(candidates and len({name for name, _, _ in candidates}) == len(candidates), "empty assembly candidate names must be distinct")
    for name, path, expected in candidates:
        AuthorCurves.require(name and path.name == name + ".SLDASM" and not path.is_relative_to(checkout) and digest(path) == expected, "candidate path or artifact identity differs")
    output.mkdir(parents=True, exist_ok=False)
    report_path = output / "Inspection.json"
    report = {"schema": "kit.sw2026.empty-assembly-candidate-probe.v1", "started_at": time.time(), "job_sha256": digest(job_path), "tool_sha256": digest(Path(__file__)), "generator": job["generator"], "controls": [], "native_empty": [], "candidates": [], "heldout_acceptance": False, "passed": False}

    def checkpoint():
        report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    def part_control(label):
        row = {"kind": label}
        report["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = healthy(row) and row["oracle_identity"]["sha256"] == job["oracle_sha256"]
        checkpoint()

    def assembly(label, path, expected_sha, *, save_copy=False):
        return inspect_assembly(path=path, expected_sha=expected_sha, directory=output / label, oracle_sha=job["oracle_sha256"], save_copy=save_copy)

    checkpoint()
    try:
        part_control("control_before")
        for phase in ("before", "after"):
            report["native_empty"].append(assembly("native-" + phase, native, job["native_empty_sha256"]))
            checkpoint()
            if phase == "before":
                for name, path, expected in candidates:
                    first = assembly(name + "-open", path, expected, save_copy=True)
                    row = {"name": name, "open": first}
                    report["candidates"].append(row)
                    checkpoint()
                    if first["passed"]:
                        row["reopen"] = assembly(name + "-reopen", Path(first["saved_path"]), first["saved_sha256"])
                        checkpoint()
        part_control("control_after")
        report["controls_healthy"] = all(row.get("healthy") for row in report["controls"]) and all(row.get("passed") for row in report["native_empty"]) and digest(control) == job["control_sha256"]
        for row in report["candidates"]:
            first, reopen = row["open"], row.get("reopen", {})
            row["matches_discovery_control"] = bool(report["controls_healthy"] and first["passed"] and reopen.get("passed") and all(
                first[key] == report["native_empty"][0]["rebuilt"] for key in ("initial", "rebuilt", "saved")
            ) and all(reopen[key] == report["native_empty"][1]["rebuilt"] for key in ("initial", "rebuilt")))
        launches = report["controls"] + report["native_empty"] + [value for row in report["candidates"] for key, value in row.items() if key in ("open", "reopen")]
        times = [entry["oracle_identity"]["process_creation_filetime"] for entry in launches if "oracle_identity" in entry]
        report["distinct_launches"] = len(set(times))
        report["passed"] = bool(len(times) == report["distinct_launches"] == len(launches) == 4 + 2 * len(candidates) and report["controls_healthy"] and all(row["matches_discovery_control"] for row in report["candidates"]))
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        report["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": report["passed"], "controls_healthy": report.get("controls_healthy"), "opened": [row["open"]["opened"] for row in report["candidates"]]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
