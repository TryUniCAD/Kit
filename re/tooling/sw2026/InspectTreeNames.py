from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from InspectCircleSketch import digest, initial_state, snapshot
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity


def run_phase(case, phase, source, output, oracle_sha256, checkpoint):
    directory = output / case["name"] / phase
    directory.mkdir(parents=True, exist_ok=False)
    recorder = AuthorCurves.Recorder(directory / "Record.json", {"case": case, "phase": phase})
    result = {"phase": phase, "source": str(source), "source_sha256": digest(source), "passed": False}
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("fresh oracle idle guard", Swapp.sweep)
            controller = recorder.call("start owned oracle", Swapp.Sw)
            identity = recorder.call("oracle executable identity", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == oracle_sha256 and controller.revision == "34.5.2", "tree observer oracle identity differs")
            result["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            author.model, errors, warnings = recorder.call("open generated tree candidate", controller.open, source)
            AuthorCurves.require(author.model is not None and errors == warnings == 0, f"tree observer load failed or warned: {errors}, {warnings}")
            result.update(open_errors=errors, open_warnings=warnings, initial_state=initial_state(author, case))
            AuthorCurves.require(result["initial_state"]["passed"], "tree candidate failed before explicit rebuild")
            result["after_open_tree"] = author.feature_tree()
            result["snapshot"] = snapshot(author, case)
            result["after_rebuild_tree"] = author.feature_tree()
            saved = directory / (case["name"] + "TreeSaved.SLDPRT")
            saved_result = recorder.call("save recursive tree candidate copy", controller.save_as, author.model, saved)
            AuthorCurves.require(saved_result == (True, 0, 0), f"tree observer save failed or warned: {saved_result}")
            result.update(saved_path=str(saved), saved_sha256=digest(saved), saved_bytes=saved.stat().st_size)
            result["after_save_tree"] = author.feature_tree()
            AuthorCurves.require(digest(saved) == result["saved_sha256"], "tree observation changed the saved file")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            try:
                if author is not None and author.model is not None:
                    recorder.call("close owned tree candidate", controller.close_doc, author.model)
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
    recorder.data.update(passed=result["passed"], tree_result=result, finished_at=time.time())
    recorder.flush()
    checkpoint()
    return result


def main():
    source = Path(sys.argv[1])
    job = json.loads(source.read_bytes())
    output = Path(job["output"])
    root = Path(job["checkout_root"]).resolve()
    AuthorCurves.require(not output.resolve().is_relative_to(root), "tree observer output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    control = Path(job["control"])
    AuthorCurves.require(digest(control) == job["control_sha256"], "tree observer control identity changed")
    result = {"schema": "kit.sw2026.recursive-tree-inspection.v1", "scope": "Recursive feature-tree observations at load, explicit rebuild, save and fresh reopen; existing source walker semantics, no writer repair or acceptance", "started_at": time.time(), "generator": job["generator"], "inspection_source_revision": job["inspection_source_revision"], "job_sha256": digest(source), "tool_sha256": digest(Path(__file__)), "cases": [], "controls": [], "full_tree_parity": False, "native_acceptance": False, "heldout_acceptance": False, "passed": False}

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
                AuthorCurves.require(digest(path) == case["sha256"], "tree candidate identity changed")
                record = {"name": case["name"], "phases": []}
                result["cases"].append(record)
                first = run_phase(case, "open-save", path, output, job["oracle_sha256"], checkpoint)
                record["phases"].append(first)
                if first["passed"]:
                    record["phases"].append(run_phase(case, "fresh-reopen", Path(first["saved_path"]), output, job["oracle_sha256"], checkpoint))
                identities = [row["oracle_identity"] for row in record["phases"] if "oracle_identity" in row]
                record["fresh_process"] = len(identities) == 2 and len({row["process_id"] for row in identities}) == len({row["process_creation_filetime"] for row in identities}) == 2
                record["passed"] = len(record["phases"]) == 2 and record["fresh_process"] and all(row["passed"] for row in record["phases"])
                checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        after = {"kind": "control_after"}
        result["controls"].append(after)
        inspect(control, result=after, checkpoint=checkpoint)
        after["healthy"] = healthy(after) and after["oracle_identity"]["sha256"] == job["oracle_sha256"]
        result["controls_healthy"] = len(result["controls"]) == 2 and all(row.get("healthy") for row in result["controls"])
        result["control_immutable"] = digest(control) == job["control_sha256"]
        result["passed"] = result["controls_healthy"] and result["control_immutable"] and bool(job["cases"]) and len(result["cases"]) == len(job["cases"]) and all(row.get("passed") is True for row in result["cases"]) and not result.get("exception")
        result["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": result["passed"], "cases": len(result["cases"]), "full_tree_parity": False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
