from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from InspectCircleSketch import digest
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity
from ProbeViewState import apply_pose, compare_pose, read_pose


def run_phase(case, phase, output, oracle, checkpoint, prior=None):
    directory = output / case["name"] / phase
    directory.mkdir(parents=True, exist_ok=False)
    recorder = AuthorCurves.Recorder(directory / "Record.json", {"case": case, "phase": phase})
    result = {"phase": phase, "passed": False}
    controller = author = preference = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("native source idle guard", Swapp.sweep)
            controller = recorder.call("start owned visible source oracle", Swapp.Sw, visible=True)
            identity = recorder.call("source oracle identity", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == oracle and controller.revision == "34.5.2", "source view oracle identity differs")
            result["oracle_identity"] = identity
            preference = bool(recorder.call("read dimension prompt preference", controller.app.GetUserPreferenceToggle, 10))
            recorder.call("disable dimension prompt", controller.app.SetUserPreferenceToggle, 10, False)
            AuthorCurves.require(not bool(recorder.call("verify disabled dimension prompt", controller.app.GetUserPreferenceToggle, 10)), "dimension prompt remains enabled")
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            if prior is None:
                author.build(case, controller)
                result["geometry"] = author.snapshot(case, "authored_geometry")
                result["saved_pose"] = apply_pose(author, case["view_request"])
                saved = directory / (case["name"] + ".SLDPRT")
                status = recorder.call("save independently authored view source", controller.save_as, author.model, saved)
                AuthorCurves.require(status == (True, 0, 0), "independent view source save failed or warned")
                author.refresh_dimension_names()
                result.update(native_path=str(saved), native_sha256=digest(saved), native_bytes=saved.stat().st_size, dimensions=copy.deepcopy(author.dimensions), requested_relations=copy.deepcopy(author.relations), after_save_pose=read_pose(author))
                compare_pose(author, result["after_save_pose"], result["saved_pose"], "source live after save")
            else:
                saved = Path(prior["native_path"])
                AuthorCurves.require(digest(saved) == prior["native_sha256"], "locked native source changed before reopening")
                author.load_relation_bindings(case, prior["requested_relations"])
                author.model, errors, warnings = recorder.call("open independently authored view source", controller.open, saved)
                AuthorCurves.require(author.model is not None and errors == warnings == 0, "independent view source reopen failed or warned")
                result.update(native_path=str(saved), native_sha256=digest(saved), native_bytes=saved.stat().st_size, open_errors=errors, open_warnings=warnings, initial_pose=read_pose(author))
                compare_pose(author, result["initial_pose"], prior["saved_pose"], "source fresh initial")
                result["geometry"] = author.snapshot(case, "reopened_geometry")
                result["after_rebuild_pose"] = read_pose(author)
                compare_pose(author, result["after_rebuild_pose"], prior["saved_pose"], "source fresh rebuilt")
                for item in prior["dimensions"]:
                    parameter = author.get(author.model, "Parameter", item["name"])
                    AuthorCurves.require(parameter is not None and int(author.get(parameter, "DrivenState")) == 2 and not bool(author.get(parameter, "ReadOnly")), "native source dimension is not editable and driving")
                    recorder.close_number("source driving " + item["role"], author.get(parameter, "SystemValue"), item["value"])
                result["source_immutable"] = digest(saved) == prior["native_sha256"]
                AuthorCurves.require(result["source_immutable"], "source verification changed the locked file")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    recorder.call("close owned source document", controller.close_doc, author.model)
                    author.model = None
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if controller is not None and preference is not None:
                try:
                    recorder.call("restore dimension prompt", controller.app.SetUserPreferenceToggle, 10, preference)
                    AuthorCurves.require(bool(recorder.call("read restored dimension prompt", controller.app.GetUserPreferenceToggle, 10)) == preference, "source dimension preference was not restored")
                    result["dimension_preference_restored"] = True
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    if prior is not None:
        result["source_immutable"] = digest(Path(prior["native_path"])) == prior["native_sha256"]
    result["passed"] = result["passed"] and result.get("source_immutable", True) and result.get("dimension_preference_restored") is True and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"] and not result.get("controller_diagnostics") and not result["dialogs"]
    recorder.data.update(source_result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    result["record_sha256"] = digest(directory / "Record.json")
    result["numeric_check_count"] = len(recorder.data["checks"])
    checkpoint()
    return result


def main():
    job_path = Path(sys.argv[1])
    job = json.loads(job_path.read_bytes())
    specs_path = Path(job["specs"])
    AuthorCurves.require(digest(specs_path) == job["specs_sha256"], "source view specifications changed")
    specs = json.loads(specs_path.read_bytes())
    AuthorCurves.require(specs["schema"] == "kit.sw2026.unseen-view-specs.v1" and len(specs["cases"]) == 2 and all(c["split"] == "heldout" for c in specs["cases"]), "complete source view cohort is required")
    output = Path(job["output"])
    AuthorCurves.require(not output.resolve().is_relative_to(Path(job["checkout_root"]).resolve()), "view source output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    control = Path(job["control"])
    AuthorCurves.require(digest(control) == job["control_sha256"], "source view control changed")
    result = {"schema": "kit.sw2026.unseen-view-source.v1", "source_revision": job["source_revision"], "job_sha256": digest(job_path), "specs_sha256": digest(specs_path), "tool_sha256": digest(Path(__file__)), "started_at": time.time(), "cases": [], "controls": [], "passed": False, "native_acceptance": False, "heldout_acceptance": False, "writer_output_count": 0}

    def checkpoint():
        AuthorCurves.write_json(output / "PrivateInspection.json", result)

    checkpoint()
    before = {"kind": "control_before"}
    result["controls"].append(before)
    inspect(control, result=before, checkpoint=checkpoint)
    before["healthy"] = healthy(before) and before["oracle_identity"]["sha256"] == job["oracle_sha256"]
    try:
        if before["healthy"]:
            for case in specs["cases"]:
                record = {"name": case["name"], "split": "heldout", "phases": []}
                result["cases"].append(record)
                first = run_phase(case, "author", output, job["oracle_sha256"], checkpoint)
                record["phases"].append(first)
                if first["passed"]:
                    record["phases"].append(run_phase(case, "fresh-reopen", output, job["oracle_sha256"], checkpoint, first))
                identities = [p["oracle_identity"] for p in record["phases"] if "oracle_identity" in p]
                record["fresh_process"] = len(identities) == 2 and len({x["process_creation_filetime"] for x in identities}) == 2
                record["passed"] = len(record["phases"]) == 2 and record["fresh_process"] and all(p["passed"] for p in record["phases"])
                checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        after = {"kind": "control_after"}
        result["controls"].append(after)
        inspect(control, result=after, checkpoint=checkpoint)
        after["healthy"] = healthy(after) and after["oracle_identity"]["sha256"] == job["oracle_sha256"]
        result["controls_healthy"] = len(result["controls"]) == 2 and all(c.get("healthy") for c in result["controls"])
        result["control_immutable"] = digest(control) == job["control_sha256"]
        result["passed"] = result["controls_healthy"] and result["control_immutable"] and len(result["cases"]) == 2 and all(c.get("passed") for c in result["cases"]) and not result.get("exception")
        result["finished_at"] = time.time()
        checkpoint()
        public = {"schema": "kit.sw2026.unseen-view-source-lock.v1", "passed": result["passed"], "source_revision": job["source_revision"], "job_sha256": result["job_sha256"], "specs_sha256": result["specs_sha256"], "private_inspection_sha256": digest(output / "PrivateInspection.json"), "controls_healthy": result["controls_healthy"], "control_immutable": result["control_immutable"], "started_at": result["started_at"], "finished_at": result["finished_at"], "writer_output_count": 0, "native_acceptance": False, "heldout_acceptance": False, "payload_and_api_observations_sealed_until_writer_freeze": True, "cases": []}
        for case in result["cases"]:
            first = case["phases"][0]
            public["cases"].append({"name": case["name"], "split": "heldout", "passed": case["passed"], "fresh_process": case["fresh_process"], "phases": len(case["phases"]), "native_file": str(Path(first["native_path"]).relative_to(output)) if "native_path" in first else None, "native_sha256": first.get("native_sha256"), "native_bytes": first.get("native_bytes"), "record_sha256": [p["record_sha256"] for p in case["phases"]], "numeric_check_count": sum(p["numeric_check_count"] for p in case["phases"])})
        AuthorCurves.write_json(output / "SourceLock.json", public)
    print(json.dumps({"passed": result["passed"], "cases": len(result["cases"]), "native_acceptance": False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
