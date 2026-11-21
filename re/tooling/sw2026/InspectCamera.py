from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from InspectCircleSketch import digest, edit_dimensions, initial_state, snapshot
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity
from ProbeViewState import compare_pose, read_pose


def run_phase(case, phase, source, output, oracle, checkpoint, factors=(1.0, 1.0, 1.0)):
    directory = output / case["name"] / phase
    directory.mkdir(parents=True, exist_ok=False)
    recorder = AuthorCurves.Recorder(directory / "Record.json", {"case": case, "phase": phase})
    result = {"phase": phase, "source": str(source), "source_sha256": digest(source), "passed": False, "view_setters_called": False}
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("fresh camera oracle idle guard", Swapp.sweep)
            controller = recorder.call("start owned visible camera oracle", Swapp.Sw, visible=True)
            identity = recorder.call("camera oracle executable identity", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == oracle and controller.revision == "34.5.2", "camera oracle identity differs")
            result["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            author.model, errors, warnings = recorder.call("open generated camera candidate without setting any view", controller.open, source)
            AuthorCurves.require(author.model is not None and errors == warnings == 0, f"camera candidate load failed or warned: {errors}, {warnings}")
            result["initial_pose"] = read_pose(author)
            result.update(open_errors=errors, open_warnings=warnings, initial_state=initial_state(author, case))
            AuthorCurves.require(result["initial_state"]["passed"], "camera candidate failed initial native body and feature checks")
            result["snapshot"] = snapshot(author, case, *factors)
            result["after_rebuild_pose"] = read_pose(author)
            compare_pose(author, result["initial_pose"], case["expected_pose"], "independent source initial")
            compare_pose(author, result["after_rebuild_pose"], case["expected_pose"], "independent source rebuilt")
            if phase == "edit-save":
                factors = edit_dimensions(author, case, result)
                result["after_edit_pose"] = read_pose(author)
                compare_pose(author, result["after_edit_pose"], case["expected_pose"], "independent source edited")
            saved = directory / (case["name"] + "CameraSaved.SLDPRT")
            status = recorder.call("save generated camera candidate copy", controller.save_as, author.model, saved)
            AuthorCurves.require(status == (True, 0, 0), f"camera candidate save failed or warned: {status}")
            result.update(saved_path=str(saved), saved_sha256=digest(saved), saved_bytes=saved.stat().st_size, saved_factors=list(factors), after_save_pose=read_pose(author))
            compare_pose(author, result["after_save_pose"], case["expected_pose"], "independent source saved")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            try:
                if author is not None and author.model is not None:
                    recorder.call("close owned camera candidate", controller.close_doc, author.model)
                    author.model = None
            except Exception as error:
                recorder.failure(error, cleanup=True)
            finally:
                if controller is not None:
                    try:
                        controller.close()
                    except Exception as error:
                        recorder.failure(error, cleanup=True)
                    result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["source_immutable"] = digest(source) == result["source_sha256"]
    result["passed"] = result["passed"] and result["source_immutable"] and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"] and not result.get("controller_diagnostics") and not result["dialogs"]
    recorder.data.update(passed=result["passed"], camera_result=result, finished_at=time.time())
    recorder.flush()
    result["record_sha256"] = digest(directory / "Record.json")
    result["numeric_check_count"] = len(recorder.data["checks"])
    checkpoint()
    return result


def main():
    job_path = Path(sys.argv[1])
    job = json.loads(job_path.read_bytes())
    output = Path(job["output"])
    AuthorCurves.require(not output.resolve().is_relative_to(Path(job["checkout_root"]).resolve()), "camera inspection output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    reference = Path(job["reference_inspection"])
    AuthorCurves.require(digest(reference) == job["reference_inspection_sha256"], "independent native source observations changed")
    references = json.loads(reference.read_bytes())
    AuthorCurves.require(references["passed"] and references["controls_healthy"] and references["control_immutable"], "independent native source observations did not pass their controls")
    expected = {case["name"]: case["phases"][0]["saved_pose"] for case in references["cases"]}
    AuthorCurves.require(len(job["cases"]) == len(expected) == 2 and {case["name"] for case in job["cases"]} == set(expected), "complete locked camera cohort is required")
    for case in job["cases"]:
        AuthorCurves.require(case["expected_pose"] == expected[case["name"]], "camera expectation differs from the independent locked source")
    control = Path(job["control"])
    AuthorCurves.require(digest(control) == job["control_sha256"], "camera inspection control changed")
    result = {"schema": "kit.sw2026.heldout-camera-inspection.v1", "scope": "Frozen camera predictions compared with independent native source poses before view setters, after rebuild, after dimension edits, after save and in fresh processes", "started_at": time.time(), "generator": job["generator"], "inspection_source_revision": job["inspection_source_revision"], "reference_inspection_sha256": job["reference_inspection_sha256"], "job_sha256": digest(job_path), "tool_sha256": digest(Path(__file__)), "writer_freeze_sha256": job["writer_freeze_sha256"], "cases": [], "controls": [], "native_acceptance": False, "heldout_acceptance": False, "passed": False}

    def checkpoint():
        AuthorCurves.write_json(output / "Inspection.json", result)

    checkpoint()
    before = {"kind": "control_before"}
    result["controls"].append(before)
    inspect(control, result=before, checkpoint=checkpoint)
    before["healthy"] = healthy(before) and before["oracle_identity"]["sha256"] == job["oracle_sha256"]
    try:
        if before["healthy"]:
            for case in job["cases"]:
                source = Path(case["path"])
                AuthorCurves.require(digest(source) == case["sha256"], "generated camera input changed before native inspection")
                record = {"name": case["name"], "phases": [], "source_sha256": case["sha256"]}
                result["cases"].append(record)
                first = run_phase(case, "open-save", source, output, job["oracle_sha256"], checkpoint)
                record["phases"].append(first)
                if first["passed"]:
                    second = run_phase(case, "edit-save", Path(first["saved_path"]), output, job["oracle_sha256"], checkpoint)
                    record["phases"].append(second)
                    if second["passed"]:
                        record["phases"].append(run_phase(case, "edited-fresh", Path(second["saved_path"]), output, job["oracle_sha256"], checkpoint, tuple(second["saved_factors"])))
                identities = [phase["oracle_identity"] for phase in record["phases"] if "oracle_identity" in phase]
                record["fresh_process"] = len(identities) == 3 and len({item["process_creation_filetime"] for item in identities}) == 3
                record["source_immutable"] = digest(source) == case["sha256"]
                record["passed"] = len(record["phases"]) == 3 and record["fresh_process"] and record["source_immutable"] and all(phase["passed"] for phase in record["phases"])
                checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        after = {"kind": "control_after"}
        result["controls"].append(after)
        inspect(control, result=after, checkpoint=checkpoint)
        after["healthy"] = healthy(after) and after["oracle_identity"]["sha256"] == job["oracle_sha256"]
        identities = [item["oracle_identity"] for item in result["controls"] if "oracle_identity" in item] + [phase["oracle_identity"] for case in result["cases"] for phase in case["phases"] if "oracle_identity" in phase]
        result["fresh_processes"] = len({item["process_creation_filetime"] for item in identities}) == len(identities) == 8
        result["controls_healthy"] = len(result["controls"]) == 2 and all(item.get("healthy") for item in result["controls"])
        result["control_immutable"] = digest(control) == job["control_sha256"]
        result["reference_immutable"] = digest(reference) == job["reference_inspection_sha256"]
        result["passed"] = result["fresh_processes"] and result["controls_healthy"] and result["control_immutable"] and result["reference_immutable"] and len(result["cases"]) == 2 and all(case.get("passed") for case in result["cases"]) and not result.get("exception")
        result["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": result["passed"], "cases": len(result["cases"]), "native_acceptance": False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
