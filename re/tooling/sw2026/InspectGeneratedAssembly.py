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


def probe(job, path, expected_sha, phase, directory, *, save):
    directory.mkdir()
    recorder = AuthorCurves.Recorder(directory / "Record.json", {"phase": phase, "source_sha256": expected_sha})
    result = {"phase": phase, "opened": False, "passed": False, "sha256": expected_sha}
    child = Path(job["child"])
    controller = model = None
    with AssemblyLoadMonitor() as monitor:
        try:
            AuthorCurves.require(digest(path) == expected_sha and digest(child) == job["child_sha256"], "generated assembly or child input changed")
            recorder.call("check idle vendor process", Swapp.sweep)
            controller = recorder.call("launch clean vendor process", Swapp.Sw)
            identity = recorder.call("check pinned executable", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"], "unexpected SOLIDWORKS executable")
            result["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = recorder.call("open generated assembly", controller.open, path, read_only=not save)
            result.update(opened=model is not None, errors=errors, warnings=warnings)
            AuthorCurves.require(model is not None and errors == 0, "generated assembly open failed")
            assembly = author.typed(model, "AssemblyDoc")
            result["components_after_open"] = int(author.get(assembly, "GetComponentCount", True))
            result["rebuild_return"] = bool(recorder.call("force rebuild generated assembly", author.get, model, "ForceRebuild3", False))
            AuthorCurves.require(result["rebuild_return"], "generated assembly rebuild failed")
            result["after_rebuild"] = recorder.call("measure resolved occurrences and geometry", snapshot, author, model, assembly, job["placements"], child, job["child_mass"], phase)
            AuthorCurves.require(all(entry["configuration"] == job["child_configuration"] for entry in result["after_rebuild"]["occurrences"]), "generated assembly selected the wrong child configuration")
            if save:
                saved = directory / "NativeSaved.SLDASM"
                result["save_status"] = list(recorder.call("save assembly to a separate file", controller.save_as, model, saved))
                AuthorCurves.require(result["save_status"] == [True, 0, 0], "generated assembly save failed or warned")
                result.update(saved_path=str(saved), saved_sha256=digest(saved))
            result["passed"] = warnings == 0
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if model is not None:
                recorder.call("close owned assembly document", controller.close_doc, model)
            if controller is not None:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=monitor.log, source_immutable=digest(path) == expected_sha, child_immutable=digest(child) == job["child_sha256"])
    result["passed"] = bool(result["passed"] and result["source_immutable"] and result["child_immutable"] and not result["dialogs"] and not result.get("controller_diagnostics"))
    recorder.data.update(result=result, finished_at=time.time())
    recorder.flush()
    result["record_sha256"] = digest(directory / "Record.json")
    return result


def main():
    job_path = Path(sys.argv[1]).resolve()
    job = json.loads(job_path.read_bytes())
    AuthorCurves.require(job["schema"] == "kit.sw2026.generated-assembly-inspection-job.v1", "unexpected generated assembly job")
    assembly, child, output, control, checkout = (Path(job[key]).resolve() for key in ("assembly", "child", "output", "control", "checkout_root"))
    AuthorCurves.require(all(not path.is_relative_to(checkout) for path in (assembly, child, output, job_path)), "generated assembly inputs and report must be outside the checkout")
    AuthorCurves.require(digest(assembly) == job["assembly_sha256"] and digest(child) == job["child_sha256"] and digest(control) == job["control_sha256"], "probe input digest differs")
    AuthorCurves.require(job["placements"], "generated assembly probe requires at least one occurrence")
    output.mkdir(parents=True)
    report_path = output / "Inspection.json"
    report = {"schema": "kit.sw2026.generated-assembly-inspection.v1", "started_at": time.time(), "job_sha256": digest(job_path), "inspector_sha256": digest(Path(__file__)), "generator": job["generator"], "controls": [], "phases": [], "passed": False, "heldout_acceptance": False}

    def checkpoint():
        AuthorCurves.write_json(report_path, report)

    def control_probe(label):
        row = {"kind": label}
        report["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = bool(healthy(row) and row["sha256"] == job["control_sha256"] and row["oracle_identity"]["sha256"] == job["oracle_sha256"])
        checkpoint()
        return row["healthy"]

    try:
        if control_probe("control_before"):
            first = probe(job, assembly, job["assembly_sha256"], "generated", output / "generated", save=True)
            report["phases"].append(first)
            checkpoint()
            if "saved_sha256" in first:
                fresh = probe(job, Path(first["saved_path"]), first["saved_sha256"], "fresh-reopen", output / "fresh-reopen", save=False)
                report["phases"].append(fresh)
                checkpoint()
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        control_probe("control_after")
        report["controls_healthy"] = len(report["controls"]) == 2 and all(row["healthy"] for row in report["controls"])
        launches = [*report["controls"], *report["phases"]]
        identities = [row["oracle_identity"]["process_creation_filetime"] for row in launches if "oracle_identity" in row]
        report["distinct_oracle_processes"] = len(set(identities))
        report["passed"] = bool(report["controls_healthy"] and len(identities) == len(launches) == report["distinct_oracle_processes"] == 4 and all(row["passed"] for row in report["phases"]))
        report["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": report["passed"], "controls_healthy": report["controls_healthy"], "phases": [{key: row.get(key) for key in ("phase", "opened", "errors", "warnings", "passed")} for row in report["phases"]]}))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
