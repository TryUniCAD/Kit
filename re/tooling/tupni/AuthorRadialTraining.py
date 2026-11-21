from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sw2026"))

import AuthorCurves
import Swapp
from ExerciseSolidworks import exercise as inspect_control
from InspectFresh import healthy

PINNED_ORACLE_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"

LOCKED_SPECIFICATIONS = {
    "4c9827d10c27766f3dc9dfe05c9de16f757949def4ce7d8b1bd82e2f39e43f01": ("TrainingD04Radius", "TrainingD04Diameter"),
    "060fc61251afee7c172f731fb7c6501220f6671d0a5a9e69fb3db940028a9383": ("TrainingD19Annulus",),
}


class TrainingRecorder(AuthorCurves.Recorder):
    def __init__(self, path, job, trace, prefix):
        self.trace, self.prefix = trace, prefix
        super().__init__(path, job)

    def call(self, label, function, *args, parameters=None, **kwargs):
        self.trace.markphase((self.prefix + f":{len(self.data['api_calls'])}:" + label)[:120])
        return super().call(label, function, *args, parameters=parameters, **kwargs)


def close_owned(author, controller, rec, trace):
    if author.model is not None:
        trace.resettrainingobjects(False)
        rec.call("close-owned-document", controller.close_doc, author.model)
        author.model = None


def run_case(controller, trace, case, directory, phase, source, oracle_identity):
    directory.mkdir(exist_ok=False)
    reset = trace.resettrainingobjects(True)
    AuthorCurves.require(reset["process_id"] == oracle_identity["process_id"], "trace and prepared controller refer to different processes")
    rec = TrainingRecorder(directory / "Record.json", {"case": case, "phase": phase}, trace, case["name"])
    author = AuthorCurves.CurveAuthor(controller.app, rec, Swapp)
    result = {"case": case, "phase": phase, "passed": False}
    original_path = None
    original_sha256 = None
    try:
        if phase == "author":
            author.build(case, controller)
            author.snapshot(case, "authored")
            target = directory / (case["name"] + ".SLDPRT")
            saved = rec.call("save-training-source", controller.save_as, author.model, target)
            AuthorCurves.require(saved == (True, 0, 0), f"training save failed or warned: {saved}")
            author.refresh_dimension_names()
            result.update(native_path=str(target), dimensions=author.dimensions, requested_relations=author.relations)
        else:
            AuthorCurves.require(source is not None and source["case"] == case and source["passed"], "training author receipt differs from the locked case")
            original_path = Path(source["native_path"])
            original_sha256 = source["sha256"]
            AuthorCurves.require(original_path.is_file() and AuthorCurves.digest(original_path) == original_sha256, "training source identity changed before reopen")
            author.load_relation_bindings(case, source["requested_relations"])
            model, errors, warnings = rec.call("reopen-training-source", controller.open, original_path)
            AuthorCurves.require(model is not None and errors == warnings == 0, f"training reopen failed or warned: {errors}, {warnings}")
            author.model = model
            author.snapshot(case, "reopened")
            dimensions = source["dimensions"]
            for item in dimensions:
                dimension = author.get(model, "Parameter", item["name"])
                AuthorCurves.require(dimension is not None, f"training dimension is missing: {item['name']}")
                AuthorCurves.require(int(author.get(dimension, "DrivenState")) == 2 and not bool(author.get(dimension, "ReadOnly")), "training dimension is not editable and driving")
                rec.close_number(item["name"], author.get(dimension, "SystemValue"), item["value"])
            selected = [item for item in dimensions if item["role"] == case["edit"]["target"]]
            AuthorCurves.require(len(selected) == 1, "training edit target is missing or ambiguous")
            item = selected[0]
            dimension = author.get(model, "Parameter", item["name"])
            value = item["value"] * case["edit"]["factor"]
            status = int(author.get(dimension, "SetSystemValue3", value, 1, Swapp.nothing()))
            AuthorCurves.require(status == 0, f"training dimension edit failed: {status}")
            rec.close_number("edited driving dimension", author.get(dimension, "SystemValue"), value)
            author.snapshot(AuthorCurves.edited_case(case), "edited")
            target = directory / (case["name"] + "Edited.SLDPRT")
            saved = rec.call("save-edited-training-copy", controller.save_as, author.model, target)
            AuthorCurves.require(saved == (True, 0, 0), f"edited training save failed or warned: {saved}")
            result.update(native_path=str(target), source_path=str(original_path), source_sha256=original_sha256, edit={"name": item["name"], "before": item["value"], "after": value, "setter_status": status})
        close_owned(author, controller, rec, trace)
        AuthorCurves.require(target.is_file(), "training save produced no file")
        result.update(sha256=AuthorCurves.digest(target), bytes=target.stat().st_size)
        if original_path is not None:
            AuthorCurves.require(AuthorCurves.digest(original_path) == original_sha256, "training edit changed the original source file")
        result["passed"] = True
    except Exception as error:
        rec.failure(error)
        raise
    finally:
        try:
            close_owned(author, controller, rec, trace)
        finally:
            trace.resettrainingobjects(False)
            rec.data.update(passed=result["passed"] and rec.data["first_failure"] is None and not rec.data["cleanup_errors"], training_result=result, finished_at=time.time())
            rec.flush()
    return result


def exercise(path, prepared):
    AuthorCurves.require(path is not None and prepared is not None and "trace" in prepared, "an explicit training job and retained traced controller are required")
    job = json.loads(path.read_text(encoding="utf-8"))
    AuthorCurves.require(job["phase"] in ("author", "reopen-edit"), "training phase must be author or reopen-edit")
    source = Path(job["specifications"])
    spec_hash = AuthorCurves.digest(source)
    AuthorCurves.require(spec_hash == job["specifications_sha256"] and spec_hash in LOCKED_SPECIFICATIONS, "training specifications are not locked")
    specifications = json.loads(source.read_text(encoding="utf-8"))
    cases = specifications["cases"]
    AuthorCurves.require(tuple(case["name"] for case in cases) == LOCKED_SPECIFICATIONS[spec_hash] and all(case["split"] == "training" for case in cases), "only the locked training cases are admitted")
    checkout = Path(job["checkout_root"]).resolve()
    output = Path(job["output"]).resolve()
    AuthorCurves.require(not output.is_relative_to(checkout) and (checkout / "AGENTS.md").is_file(), "training output must be outside the selected checkout")
    output.mkdir(parents=True, exist_ok=False)
    control = Path(job["control"])
    AuthorCurves.require(control.is_file() and AuthorCurves.digest(control) == job["control_sha256"], "training control identity differs")
    controller, trace = prepared["controller"], prepared["trace"]
    identity = prepared["identity"]["oracle_identity"]
    AuthorCurves.require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"] == PINNED_ORACLE_SHA256 and controller.revision == "34.5.2", "prepared oracle differs from the pinned installation")
    state = trace.resettrainingobjects(False)
    AuthorCurves.require(state["process_id"] == identity["process_id"], "trace and prepared controller refer to different processes")
    sources = {}
    if job["phase"] == "reopen-edit":
        source_manifest = Path(job["source_manifest"])
        source_manifest_bytes = source_manifest.read_bytes()
        source_manifest_sha256 = hashlib.sha256(source_manifest_bytes).hexdigest()
        AuthorCurves.require(source_manifest_sha256 == job["source_manifest_sha256"], "training source manifest differs from its frozen identity")
        previous = json.loads(source_manifest_bytes)
        AuthorCurves.require(previous["phase"] == "author" and previous["passed"] and previous["specifications_sha256"] == spec_hash, "training author manifest is incomplete or changed")
        prior_identity = previous["oracle_identity"]
        AuthorCurves.require(all(type(value.get("process_creation_filetime")) is int for value in (prior_identity, identity)), "fresh-process proof requires both creation identities")
        AuthorCurves.require((prior_identity["process_id"], prior_identity["process_creation_filetime"]) != (identity["process_id"], identity["process_creation_filetime"]), "reopen training requires a fresh owned process")
        sources = {item["case"]["name"]: item for item in previous["cases"]}
        AuthorCurves.require(set(sources) == {case["name"] for case in cases}, "training author manifest has different case membership")
    record = {"schema": "kit-sw2026-radial-training-result/1", "authority": "instrumented-training-authoring", "instruction_taint": False, "phase": job["phase"], "specifications_sha256": spec_hash, "oracle_identity": identity, "controls_share_instrumented_process": True, "helper_sha256": {"AuthorCurves.py": AuthorCurves.digest(AuthorCurves.__file__), "Swapp.py": AuthorCurves.digest(Swapp.__file__)}, "cases": [], "passed": False, "field_closure_proven": False, "callback_effects_proven": False, "acceptance": False}
    prepared["identity"]["measurement"] = record
    report = output / "Training.json"
    if job["phase"] == "reopen-edit":
        record["source_manifest"] = {"path": str(source_manifest), "sha256": source_manifest_sha256}
    preference = None
    failure = None
    try:
        trace.markphase("training-control-before")
        record["control_before"] = inspect_control(control, prepared)
        AuthorCurves.require(healthy(record["control_before"]), "instrumented control failed before training")
        trace.resettrainingobjects(True)
        preference = bool(Swapp.cv(controller.app, "GetUserPreferenceToggle", 10))
        record["input_dimension_preference"] = {"before": preference, "restored": False}
        controller.app.SetUserPreferenceToggle(10, False)
        AuthorCurves.require(not bool(Swapp.cv(controller.app, "GetUserPreferenceToggle", 10)), "dimension input prompt was not disabled")
        AuthorCurves.write_json(report, record)
        for case in cases:
            trace.markphase(case["name"] + ":start")
            record["cases"].append(run_case(controller, trace, case, output / case["name"], job["phase"], sources.get(case["name"]), identity))
            AuthorCurves.write_json(report, record)
    except Exception as error:
        failure = error
        record["failure"] = repr(error)
    finally:
        if preference is not None:
            try:
                controller.app.SetUserPreferenceToggle(10, preference)
                restored = bool(Swapp.cv(controller.app, "GetUserPreferenceToggle", 10)) == preference
                record["input_dimension_preference"]["restored"] = restored
                AuthorCurves.require(restored, "input dimension preference was not restored")
            except Exception as error:
                record["preference_cleanup_error"] = repr(error)
                failure = failure or error
        try:
            trace.resettrainingobjects(False)
            trace.markphase("training-control-after")
            record["control_after"] = inspect_control(control, prepared)
            AuthorCurves.require(healthy(record["control_after"]), "instrumented control failed after training")
            AuthorCurves.require(AuthorCurves.digest(control) == job["control_sha256"], "training control file changed")
            if job["phase"] == "reopen-edit":
                AuthorCurves.require(AuthorCurves.digest(source_manifest) == source_manifest_sha256, "frozen training source manifest changed")
        except Exception as error:
            record["control_after_error"] = repr(error)
            failure = failure or error
        record["passed"] = failure is None and len(record["cases"]) == len(cases)
        record["finished_at"] = time.time()
        prepared["identity"]["measurement"] = record
        AuthorCurves.write_json(report, record)
    if failure is not None:
        raise failure
    trace.markphase("training-action-complete")
    return record
