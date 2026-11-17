from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from InspectCircleSketch import digest
from InspectFresh import healthy, inspect
from ObserveAssemblyLoad import AssemblyLoadMonitor
from OracleIdentity import application_identity


def read_state(author, model, assembly):
    extension = author.get(model, "Extension")
    return {
        "needs_rebuild": int(author.get(extension, "NeedsRebuild2")),
        "save_flag": bool(author.get(model, "GetSaveFlag")),
        "whats_wrong": int(author.get(extension, "GetWhatsWrongCount")),
        "top_level_count": int(author.get(assembly, "GetComponentCount", True)),
    }


def run_phase(job, output, phase, input_path, input_hash, readonly, resave=False):
    folder = output / phase
    folder.mkdir()
    recorder = AuthorCurves.Recorder(folder / "Record.json", {"phase": phase, "source_sha256": input_hash, "read_only": readonly})
    result = {"phase": phase, "read_only": readonly, "completed": False, "source_sha256": input_hash}
    controller = model = None
    with AssemblyLoadMonitor() as monitor:
        try:
            AuthorCurves.require(digest(input_path) == input_hash, "assembly probe input changed")
            recorder.call("assembly rebuild probe idle guard", Swapp.sweep)
            controller = recorder.call("launch owned assembly rebuild probe", Swapp.Sw)
            identity = recorder.call("verify assembly rebuild probe oracle", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"], "assembly rebuild probe oracle differs")
            result["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = recorder.call("open immutable assembly probe input", controller.open, input_path, read_only=readonly)
            result.update(open_errors=errors, open_warnings=warnings)
            AuthorCurves.require(model is not None and errors == 0 and warnings in (0, 32), "unexpected assembly probe load diagnostic")
            assembly = author.typed(model, "AssemblyDoc")
            result["after_open"] = read_state(author, model, assembly)
            if resave:
                result["active_rebuild_return"] = bool(author.get(model, "ForceRebuild3", False))
                result["after_active_rebuild"] = read_state(author, model, assembly)
                result["all_rebuild_return"] = bool(author.get(author.get(model, "Extension"), "ForceRebuildAll"))
                result["after_all_rebuild"] = read_state(author, model, assembly)
                AuthorCurves.require(result["active_rebuild_return"] and result["all_rebuild_return"] and result["after_all_rebuild"]["whats_wrong"] == 0, "assembly probe rebuild failed")
                saved = folder / "RebuiltProbe.SLDASM"
                AuthorCurves.require(recorder.call("save separate rebuilt assembly probe", controller.save_as, model, saved) == (True, 0, 0), "assembly rebuild probe save failed")
                result.update(saved_path=str(saved), saved_sha256=digest(saved), saved_bytes=saved.stat().st_size, after_save=read_state(author, model, assembly))
            result["completed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if model is not None:
                try:
                    recorder.call("close owned assembly probe", controller.close_doc, model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result.update(source_immutable=digest(input_path) == input_hash, dialogs=monitor.log, progress_windows=monitor.progress)
    result["completed"] = bool(result["completed"] and result["source_immutable"] and not result["dialogs"] and not result.get("controller_diagnostics") and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result, finished_at=time.time())
    recorder.flush()
    result["record_sha256"] = digest(folder / "Record.json")
    return result


def main():
    job_path = Path(sys.argv[1])
    job = json.loads(job_path.read_bytes())
    AuthorCurves.require(job["schema"] == "kit.sw2026.assembly-rebuild-probe-job.v1", "unexpected assembly rebuild probe job")
    control, source, output = (Path(job[key]).resolve() for key in ("control", "source", "output"))
    checkout = Path(job["checkout_root"]).resolve()
    AuthorCurves.require(not output.is_relative_to(checkout) and not source.is_relative_to(checkout) and source.name == "A08SingleAssembly.SLDASM", "assembly probe must use the named external discovery source")
    AuthorCurves.require(digest(control) == job["control_sha256"] and digest(source) == job["source_sha256"], "assembly probe input hashes differ")
    output.mkdir(parents=True, exist_ok=False)
    result = {"schema": "kit.sw2026.assembly-rebuild-probe.v1", "source_revision": job["source_revision"], "job_sha256": digest(job_path), "tool_sha256": digest(Path(__file__)), "started_at": time.time(), "controls": [], "phases": [], "native_acceptance": False, "writer_output_count": 0}

    def checkpoint():
        AuthorCurves.write_json(output / "Inspection.json", result)

    def control_phase(label):
        row = {"kind": label}
        result["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = bool(healthy(row) and row["oracle_identity"]["sha256"] == job["oracle_sha256"])
        return row["healthy"]

    try:
        if control_phase("control_before"):
            result["phases"].append(run_phase(job, output, "original-readonly", source, job["source_sha256"], True))
            checkpoint()
            change = run_phase(job, output, "normal-open-rebuild-save", source, job["source_sha256"], False, True)
            result["phases"].append(change)
            checkpoint()
            if change["completed"]:
                result["phases"].append(run_phase(job, output, "fresh-rebuilt-save", Path(change["saved_path"]), change["saved_sha256"], True))
                checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        control_phase("control_after")
        result["controls_healthy"] = len(result["controls"]) == 2 and all(row.get("healthy") for row in result["controls"])
        result["inputs_immutable"] = digest(control) == job["control_sha256"] and digest(source) == job["source_sha256"]
        phases = result["phases"]
        result["diagnostic_completed"] = bool(result["controls_healthy"] and result["inputs_immutable"] and len(phases) == 3 and all(row["completed"] for row in phases) and not result.get("exception"))
        result["rebuilt_copy_reopens_without_warning"] = result["diagnostic_completed"] and phases[-1]["open_warnings"] == 0
        result["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({key: result[key] for key in ("diagnostic_completed", "rebuilt_copy_reopens_without_warning", "controls_healthy", "native_acceptance")}))
    return 0 if result["diagnostic_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
