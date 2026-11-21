from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from InspectCircleSketch import digest, edit_dimensions, initial_state, snapshot
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity
from ProbeViewState import compare_pose, read_pose


def compare_frame(author, case, result, label, values=None):
    expected = case.get("locked_profile_frame")
    if expected is None:
        return
    if values is None:
        sketch_name = case["request"]["document"]["sketch_name"]
        feature = author.get(author.model, "FeatureByName", sketch_name)
        AuthorCurves.require(feature is not None, "initial profile feature is missing")
        sketch = author.get(feature, "GetSpecificFeature2")
        transform = author.get(sketch, "ModelToSketchTransform")
        values = author.get(transform, "ArrayData")
    actual = [float(value) for value in values]
    AuthorCurves.require(len(actual) == 16 and all(math.isfinite(value) for value in actual), "invalid native profile transform")
    passed = actual[:13] == expected
    result.setdefault("profile_frame_comparisons", {})[label] = {"actual": actual, "expected": expected, "passed": passed, "exact_value_count": sum(a == b for a, b in zip(actual[:13], expected, strict=True))}
    author.rec.flush()
    AuthorCurves.require(passed, f"native profile transform differs from frozen generated archive at {label}")


def compare_scene(author, actual, expected, label, result):
    fields = ("name", "type", "parent", "suppressed")
    left = [{key: row[key] for key in fields} for row in actual["tree"]]
    right = [{key: row[key] for key in fields} for row in expected["tree"]]
    passed = left == right
    result.setdefault("tree_comparisons", {})[label] = {
        "passed": passed,
        "actual_count": len(left),
        "expected_count": len(right),
        "fields": list(fields),
        "ordered_tree_equality": passed,
    }
    author.rec.flush()
    AuthorCurves.require(passed, "ordered native tree differs from independent source at " + label)
    compare_pose(author, actual["pose"], expected["pose"], "paired source " + label)


def scene(author, result, label, reference):
    observed = {"pose": read_pose(author), "tree": author.feature_tree(), "visible_bodies": len(author.get(author.model, "GetBodies2", 0, True) or [])}
    result.setdefault("scenes", {})[label] = observed
    AuthorCurves.require(bool(observed["tree"]), "native recursive tree is empty")
    AuthorCurves.require(observed["visible_bodies"] == 1, "paired native input must have one visible solid body")
    if reference is not None:
        compare_scene(author, observed, reference["scenes"][label], label, result)
    return observed


def run_phase(case, lane, phase, source, output, oracle, checkpoint, reference=None, factors=(1.0, 1.0, 1.0)):
    directory = output / case["name"] / lane / phase
    directory.mkdir(parents=True, exist_ok=False)
    recorder = AuthorCurves.Recorder(directory / "Record.json", {"case": case, "lane": lane, "phase": phase})
    result = {"lane": lane, "phase": phase, "source_sha256": digest(source), "passed": False, "view_setters_called": False}
    recorder.data["tree_result"] = result
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("paired tree oracle idle guard", Swapp.sweep)
            controller = recorder.call("start owned visible paired tree oracle", Swapp.Sw, visible=True)
            identity = recorder.call("paired tree oracle identity", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == oracle and controller.revision == "34.5.2", "paired tree oracle identity differs")
            result["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            author.model, errors, warnings = recorder.call("open immutable paired tree input", controller.open, source)
            AuthorCurves.require(author.model is not None and errors == warnings == 0, "paired tree input failed or warned during load")
            result.update(open_errors=errors, open_warnings=warnings)
            initial = scene(author, result, "initial", reference)
            if lane == "reference" and phase == "open-save":
                compare_scene(author, initial, case["locked_source_scene"], "locked source initial", result)
            compare_frame(author, case, result, "initial")
            result["initial_state"] = initial_state(author, case)
            AuthorCurves.require(result["initial_state"]["passed"], "paired tree input has no initial body or unhealthy features")
            result["snapshot"] = snapshot(author, case, *factors)
            compare_frame(author, case, result, "rebuilt", result["snapshot"]["model_to_sketch_transform"])
            scene(author, result, "rebuilt", reference)
            if phase == "edit-save":
                factors = edit_dimensions(author, case, result)
                if "locked_profile_frame" in case:
                    for label, key in (("radial-edit", "edited_snapshot"), ("depth-edit", "edited_body_snapshot")):
                        compare_frame(author, case, result, label, result[key]["model_to_sketch_transform"])
                scene(author, result, "edited", reference)
            saved = directory / (case["name"] + "PairedSaved.SLDPRT")
            status = recorder.call("save owned paired tree copy", controller.save_as, author.model, saved)
            AuthorCurves.require(status == (True, 0, 0), "paired tree save failed or warned")
            result.update(saved_path=str(saved), saved_sha256=digest(saved), saved_bytes=saved.stat().st_size, saved_factors=list(factors))
            compare_frame(author, case, result, "saved")
            scene(author, result, "saved", reference)
            AuthorCurves.require(digest(saved) == result["saved_sha256"], "post-save observation changed the native copy")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            try:
                if author is not None and author.model is not None:
                    recorder.call("close owned paired tree document", controller.close_doc, author.model)
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
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress, source_immutable=digest(source) == result["source_sha256"])
    result["passed"] = result["passed"] and result["source_immutable"] and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"] and not result.get("controller_diagnostics") and not result["dialogs"]
    recorder.data.update(passed=result["passed"], finished_at=time.time())
    recorder.flush()
    result.update(record_sha256=digest(directory / "Record.json"), numeric_check_count=len(recorder.data["checks"]))
    checkpoint()
    return result


def run_lane(case, lane, source, output, oracle, checkpoint, reference=None):
    phases = []
    for phase, factors in (("open-save", (1.0, 1.0, 1.0)), ("edit-save", (1.0, 1.0, 1.0)), ("edited-fresh", (case["edit_factor"], case["depth_edit_factor"], 1.0))):
        expected = None if reference is None else next(row for row in reference if row["phase"] == phase)
        result = run_phase(case, lane, phase, source, output, oracle, checkpoint, expected, factors)
        phases.append(result)
        if not result["passed"]:
            break
        source = Path(result["saved_path"])
    return phases


def main():
    job_path = Path(sys.argv[1])
    job = json.loads(job_path.read_bytes())
    receipt_path = Path(job["prediction_receipt"])
    AuthorCurves.require(digest(receipt_path) == job["prediction_receipt_sha256"], "prediction receipt changed")
    receipt = json.loads(receipt_path.read_bytes())
    AuthorCurves.require(receipt["passed"] and receipt["generated_outputs"] == 2 and receipt["complete_archive_comparisons"] == 16, "complete frozen predictions must pass before reference access")
    AuthorCurves.require(receipt["changed_constructor_dependencies"] == [] and job["writer_freeze_sha256"] == receipt["writer_freeze_sha256"], "prediction writer identity changed")
    predictions = {row["name"]: row for row in receipt["outputs"]}
    AuthorCurves.require(len(job["cases"]) == len(predictions) == 2 and {row["name"] for row in job["cases"]} == set(predictions), "complete prediction cohort is required")
    frame_batch = receipt["schema"] == "kit.sw2026.frame-heldout-processes.v1"
    if frame_batch:
        AuthorCurves.require(job["generator"] == receipt["writer_revision"] and receipt["profile_model_to_sketch_checks"] == 26, "corrected profile prediction identities or checks differ")
        AuthorCurves.require(receipt["private_reference_api_observations_inspected"] is receipt["native_reference_payloads_inspected"] is False, "frame predictions already accessed the native sources")
    for case in job["cases"]:
        prediction = predictions[case["name"]]
        AuthorCurves.require(case["request"] == prediction["request"] and case["sha256"] == prediction["sha256"], "inspection request differs from frozen prediction")
        AuthorCurves.require("locked_profile_frame" not in case, "profile frame must come from the frozen prediction receipt")
        if frame_batch:
            expected = prediction["profile_model_to_sketch"]
            AuthorCurves.require(len(expected) == 13 and all(type(value) in (int, float) and math.isfinite(value) for value in expected) and expected[-1] == 1, "prediction profile transform is incomplete")
            case["locked_profile_frame"] = expected
    source_lock_path = Path(job["source_lock"])
    AuthorCurves.require(digest(source_lock_path) == receipt["source_lock_sha256"], "public source lock changed")
    source_lock = json.loads(source_lock_path.read_bytes())
    AuthorCurves.require(source_lock["passed"] and source_lock["controls_healthy"] and source_lock["private_inspection_sha256"] == job["reference_inspection_sha256"], "private reference does not match the public source lock")
    output = Path(job["output"])
    AuthorCurves.require(not output.resolve().is_relative_to(Path(job["checkout_root"]).resolve()), "paired tree output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    private = Path(job["reference_inspection"])
    AuthorCurves.require(digest(private) == job["reference_inspection_sha256"], "locked source observations changed")
    observations = json.loads(private.read_bytes())
    AuthorCurves.require(observations["passed"] and observations["controls_healthy"] and observations["control_immutable"], "source observations did not pass controls")
    references = {row["name"]: row for row in observations["cases"]}
    AuthorCurves.require(len(job["cases"]) == len(references) == 2 and {row["name"] for row in job["cases"]} == set(references), "complete source and prediction cohorts must match")
    for case in job["cases"]:
        original = references[case["name"]]["phases"][0]
        source = Path(case["reference_path"])
        AuthorCurves.require(digest(source) == case["reference_sha256"] == original["native_sha256"], "reference native source changed")
        AuthorCurves.require(digest(Path(case["path"])) == case["sha256"], "generated prediction changed")
        case["locked_source_scene"] = {"pose": original["saved_pose"], "tree": original["geometry"]["feature_tree"]}
    control = Path(job["control"])
    AuthorCurves.require(digest(control) == job["control_sha256"], "paired tree control changed")
    result = {"schema": "kit.sw2026.paired-tree-inspection.v1", "scope": "Frozen generated tree predictions compared with independent native source trajectories through identical edits save and fresh reopen", "started_at": time.time(), "inspection_source_revision": job["inspection_source_revision"], "generator": job["generator"], "prediction_receipt_sha256": digest(receipt_path), "reference_inspection_sha256": digest(private), "writer_freeze_sha256": job["writer_freeze_sha256"], "tool_sha256": digest(Path(__file__)), "job_sha256": digest(job_path), "cases": [], "controls": [], "native_acceptance": False, "heldout_acceptance": False, "passed": False}
    if frame_batch:
        result.update(schema="kit.sw2026.paired-frame-inspection.v1", scope="Persisted model-to-sketch transforms checked against both native trajectories before rebuild through edits save and reopen")

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
                record = {"name": case["name"], "reference": [], "candidate": [], "passed": False}
                result["cases"].append(record)
                record["reference"] = run_lane(case, "reference", Path(case["reference_path"]), output, job["oracle_sha256"], checkpoint)
                if len(record["reference"]) == 3 and all(p["passed"] for p in record["reference"]):
                    record["candidate"] = run_lane(case, "candidate", Path(case["path"]), output, job["oracle_sha256"], checkpoint, record["reference"])
                identities = [p["oracle_identity"] for lane in ("reference", "candidate") for p in record[lane] if "oracle_identity" in p]
                record["fresh_processes"] = len(identities) == 6 and len({x["process_creation_filetime"] for x in identities}) == 6
                record["passed"] = record["fresh_processes"] and len(record["candidate"]) == 3 and all(p["passed"] for p in record["reference"] + record["candidate"])
                checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        after = {"kind": "control_after"}
        result["controls"].append(after)
        inspect(control, result=after, checkpoint=checkpoint)
        after["healthy"] = healthy(after) and after["oracle_identity"]["sha256"] == job["oracle_sha256"]
        result["controls_healthy"] = len(result["controls"]) == 2 and all(row.get("healthy") for row in result["controls"])
        result["inputs_immutable"] = digest(control) == job["control_sha256"] and digest(private) == job["reference_inspection_sha256"] and all(digest(Path(case[key])) == case[sha] for case in job["cases"] for key, sha in (("path", "sha256"), ("reference_path", "reference_sha256")))
        identities = [row["oracle_identity"] for row in result["controls"] if "oracle_identity" in row]
        identities.extend(phase["oracle_identity"] for row in result["cases"] for lane in ("reference", "candidate") for phase in row[lane] if "oracle_identity" in phase)
        result["all_fresh_processes"] = len(identities) == 14 and len({row["process_creation_filetime"] for row in identities}) == 14
        result["passed"] = result["controls_healthy"] and result["inputs_immutable"] and result["all_fresh_processes"] and len(result["cases"]) == 2 and all(row["passed"] for row in result["cases"]) and not result.get("exception")
        if frame_batch:
            frames = [item for case in result["cases"] for lane in ("reference", "candidate") for phase in case[lane] for item in phase.get("profile_frame_comparisons", {}).values()]
            result["profile_frame_comparison_count"] = len(frames)
            result["exact_profile_frame_value_count"] = sum(row["exact_value_count"] for row in frames)
            result["passed"] = result["passed"] and len(frames) == 44 and result["exact_profile_frame_value_count"] == 572 and all(row["passed"] for row in frames)
        result["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": result["passed"], "cases": len(result["cases"]), "native_acceptance": False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
