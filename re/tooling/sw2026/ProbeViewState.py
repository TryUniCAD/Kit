from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from InspectCircleSketch import digest, initial_state, snapshot
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity


def read_pose(author):
    view = author.get(author.model, "ActiveView")
    AuthorCurves.require(view is not None, "visible model has no active view")
    orientation = [float(x) for x in author.get(author.get(view, "Orientation3"), "ArrayData")]
    translation = [float(x) for x in author.get(author.get(view, "Translation3"), "ArrayData")]
    scale = float(author.get(view, "Scale2"))
    AuthorCurves.require(len(orientation) == 16 and len(translation) == 3 and all(math.isfinite(x) for x in [*orientation, *translation, scale]) and scale > 0, "native view pose is incomplete or nonfinite")
    return {"orientation": orientation, "translation": translation, "scale2": scale}


def compare_pose(author, actual, expected, label):
    for key, count in (("orientation", 16), ("translation", 3)):
        AuthorCurves.require(len(actual[key]) == len(expected[key]) == count, "view pose cardinality differs")
        for i, value in enumerate(expected[key]):
            author.rec.close_number(f"{label} {key} {i}", actual[key][i], value)
    author.rec.close_number(label + " scale2", actual["scale2"], expected["scale2"])


def apply_pose(author, requested):
    expected = {}
    if "named_view" in requested:
        index = requested["named_view"]
        AuthorCurves.require(type(index) is int and 1 <= index <= 9, "named view must be a supported native index")
        target = author.get(author.model, "GetStandardViewRotation", index)
        target = list(target) if isinstance(target, (list, tuple)) else list(author.get(target, "ArrayData"))
        AuthorCurves.require(len(target) == 9, "native standard view must return nine rotation coefficients")
        author.get(author.model, "ShowNamedView2", "", index)
        expected["orientation"] = [*[float(x) for x in target], *read_pose(author)["orientation"][9:]]
    view = author.get(author.model, "ActiveView")
    if "scale2" in requested:
        scale = requested["scale2"]
        AuthorCurves.require(type(scale) in (int, float) and math.isfinite(scale) and scale > 0, "view scale must be explicit finite and positive")
        author.rec.call("set Scale2", setattr, view, "Scale2", scale, parameters={"value": scale})
        expected["scale2"] = scale
    if "translation" in requested:
        values = requested["translation"]
        AuthorCurves.require(isinstance(values, list) and len(values) == 3 and all(type(x) in (int, float) and math.isfinite(x) for x in values), "view translation must be three finite native API coordinates")
        utility = author.get(author.app, "GetMathUtility")
        vector = author.get(utility, "CreateVector", Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_R8, values))
        author.rec.call("set Translation3", setattr, view, "Translation3", vector, parameters={"array_data": values})
        expected["translation"] = values
    author.get(author.model, "GraphicsRedraw2")
    actual = read_pose(author)
    compare_pose(author, actual, {**actual, **expected}, "requested")
    return actual


def run_phase(case, phase, source, output, oracle_sha256, checkpoint, expected=None):
    directory = output / case["name"] / phase
    directory.mkdir(parents=True, exist_ok=False)
    recorder = AuthorCurves.Recorder(directory / "Record.json", {"case": case, "phase": phase})
    result = {"phase": phase, "source": str(source), "source_sha256": digest(source), "passed": False}
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("fresh visible oracle idle guard", Swapp.sweep)
            controller = recorder.call("start owned visible oracle", Swapp.Sw, visible=True)
            identity = recorder.call("oracle executable identity", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == oracle_sha256 and controller.revision == "34.5.2", "view probe oracle identity differs")
            result["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            author.model, errors, warnings = recorder.call("open generated view candidate", controller.open, source)
            AuthorCurves.require(author.model is not None and errors == warnings == 0, f"view probe load failed or warned: {errors}, {warnings}")
            result.update(open_errors=errors, open_warnings=warnings, initial_pose=read_pose(author), initial_state=initial_state(author, case))
            AuthorCurves.require(result["initial_state"]["passed"], "view probe failed initial body checks")
            result["snapshot"] = snapshot(author, case)
            result["after_rebuild_pose"] = read_pose(author)
            if expected is not None:
                compare_pose(author, result["initial_pose"], expected, "fresh initial")
                compare_pose(author, result["after_rebuild_pose"], expected, "fresh rebuilt")
                result["saved_pose"] = result["after_rebuild_pose"]
            else:
                result["saved_pose"] = apply_pose(author, case["view_request"])
            saved = directory / (case["name"] + "ViewSaved.SLDPRT")
            status = recorder.call("save native view probe copy", controller.save_as, author.model, saved)
            AuthorCurves.require(status == (True, 0, 0), f"view probe save failed or warned: {status}")
            result.update(saved_path=str(saved), saved_sha256=digest(saved), saved_bytes=saved.stat().st_size, after_save_pose=read_pose(author))
            compare_pose(author, result["after_save_pose"], result["saved_pose"], "live after save")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            try:
                if author is not None and author.model is not None:
                    recorder.call("close owned visible view candidate", controller.close_doc, author.model)
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
    recorder.data.update(passed=result["passed"], view_result=result, finished_at=time.time())
    recorder.flush()
    checkpoint()
    return result


def main():
    source = Path(sys.argv[1])
    job = json.loads(source.read_bytes())
    output = Path(job["output"])
    AuthorCurves.require(not output.resolve().is_relative_to(Path(job["checkout_root"]).resolve()), "view probe output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    control = Path(job["control"])
    AuthorCurves.require(digest(control) == job["control_sha256"], "view probe control identity changed")
    result = {"schema": "kit.sw2026.visible-view-probe.v1", "scope": "Independent native view property interventions on existing generated input; training observations only, no new generated output or held-out acceptance", "started_at": time.time(), "generator": job["generator"], "inspection_source_revision": job["inspection_source_revision"], "job_sha256": digest(source), "tool_sha256": digest(Path(__file__)), "cases": [], "controls": [], "native_acceptance": False, "heldout_acceptance": False, "passed": False}

    def checkpoint():
        (output / "Inspection.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    checkpoint()
    before = {"kind": "control_before"}
    result["controls"].append(before)
    inspect(control, result=before, checkpoint=checkpoint)
    before["healthy"] = healthy(before) and before["oracle_identity"]["sha256"] == job["oracle_sha256"]
    try:
        if before["healthy"]:
            for case in job["cases"]:
                path = Path(case["path"])
                AuthorCurves.require(digest(path) == case["sha256"], "view probe generated input changed")
                record = {"name": case["name"], "phases": []}
                result["cases"].append(record)
                first = run_phase(case, "open-save", path, output, job["oracle_sha256"], checkpoint)
                record["phases"].append(first)
                if first["passed"]:
                    record["phases"].append(run_phase(case, "fresh-reopen", Path(first["saved_path"]), output, job["oracle_sha256"], checkpoint, first["saved_pose"]))
                identities = [x["oracle_identity"] for x in record["phases"] if "oracle_identity" in x]
                record["fresh_process"] = len(identities) == 2 and len({x["process_id"] for x in identities}) == len({x["process_creation_filetime"] for x in identities}) == 2
                record["passed"] = len(record["phases"]) == 2 and record["fresh_process"] and all(x["passed"] for x in record["phases"])
                checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        after = {"kind": "control_after"}
        result["controls"].append(after)
        inspect(control, result=after, checkpoint=checkpoint)
        after["healthy"] = healthy(after) and after["oracle_identity"]["sha256"] == job["oracle_sha256"]
        result["controls_healthy"] = len(result["controls"]) == 2 and all(x.get("healthy") for x in result["controls"])
        result["control_immutable"] = digest(control) == job["control_sha256"]
        result["passed"] = result["controls_healthy"] and result["control_immutable"] and bool(job["cases"]) and len(result["cases"]) == len(job["cases"]) and all(x.get("passed") is True for x in result["cases"]) and not result.get("exception")
        result["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": result["passed"], "cases": len(result["cases"]), "native_acceptance": False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
