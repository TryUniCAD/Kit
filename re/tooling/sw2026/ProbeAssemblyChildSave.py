from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from AuthorAssemblySources import placement_transform, snapshot
from InspectCircleSketch import digest
from InspectFresh import healthy, inspect
from ObserveAssemblyLoad import AssemblyLoadMonitor
from OracleIdentity import application_identity
from ProbeAssemblyRebuild import read_state


def child_document(author, assembly, child_path):
    components = author.get(assembly, "GetComponents", False) or ()
    AuthorCurves.require(len(components) == 1, "child save probe must contain one component")
    component = author.typed(components[0], "Component2")
    AuthorCurves.require(Path(author.get(component, "GetPathName")).resolve() == child_path.resolve(), "child save probe resolved a different file")
    child = author.get(component, "GetModelDoc2")
    AuthorCurves.require(child is not None and Path(author.get(child, "GetPathName")).resolve() == child_path.resolve(), "child document does not own the staged path")
    return child


def run_phase(job, output, lane, child_path, parent_path, masses, prior=None):
    phase = "author" if prior is None else "fresh-reopen"
    folder = output / lane / phase
    folder.mkdir()
    recorder = AuthorCurves.Recorder(folder / "Record.json", {"lane": lane, "phase": phase})
    row = {"phase": phase, "completed": False, "explicit_child_save": lane == "synced"}
    baseline_hash = digest(child_path)
    controller = model = None
    with AssemblyLoadMonitor() as monitor:
        try:
            Swapp.sweep()
            controller = Swapp.Sw()
            identity = application_identity(controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"], "child save diagnostic oracle differs")
            row["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            expected = [placement_transform({"axis": "z", "angle_deg": 0.0, "translation_m": [0.0, 0.0, 0.0]})]
            if prior is None:
                AuthorCurves.require(baseline_hash == job["control_sha256"], "private child seed changed")
                model = controller.new_assembly()
                assembly = author.typed(model, "AssemblyDoc")
                args = [Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | kind, value) for kind, value in ((Swapp.pythoncom.VT_BSTR, [str(child_path)]), (Swapp.pythoncom.VT_R8, expected[0]), (Swapp.pythoncom.VT_BSTR, [""]))]
                inserted = recorder.call("AddComponents3", assembly.AddComponents3, *args)
                AuthorCurves.require(inserted is not None and len(inserted) == 1, "single private child insertion failed")
                child = child_document(author, assembly, child_path)
                AuthorCurves.require(bool(author.get(model, "ForceRebuild3", False)), "private parent rebuild failed")
                author.get(child, "SetSaveFlag")
                row["before_save"] = read_state(author, model, assembly, child_path)
                AuthorCurves.require(row["before_save"]["child"]["save_flag"], "private child did not become dirty")
                row["pre_save_update_stamp"] = int(author.get(child, "GetUpdateStamp"))
                if lane == "synced":
                    errors, warnings = Swapp.byref_long(), Swapp.byref_long()
                    successful = recorder.call("save only owned child", Swapp.invoke, child, "Save3", Swapp.SAVE_SILENT, errors, warnings)
                    row["child_save_status"] = [bool(successful), int(errors.value), int(warnings.value)]
                    AuthorCurves.require(row["child_save_status"] == [True, 0, 0], "explicit child save failed or warned")
                row["child_sha256_before_parent_save"] = digest(child_path)
                status = recorder.call("save private parent", controller.save_as, model, parent_path)
                AuthorCurves.require(status == (True, 0, 0), "private parent save failed or warned")
                row["child_sha256_after_parent_save"] = digest(child_path)
            else:
                AuthorCurves.require(digest(parent_path) == prior["parent_sha256"] and baseline_hash == prior["child_sha256"], "private saved inputs changed before reopen")
                model, errors, warnings = recorder.call("open fresh private parent", controller.open, parent_path, read_only=True)
                row.update(open_errors=errors, open_warnings=warnings)
                AuthorCurves.require(model is not None and errors == 0 and warnings in (0, 32), "unexpected private parent load status")
                assembly = author.typed(model, "AssemblyDoc")
                child = child_document(author, assembly, child_path)
            row["result_state"] = read_state(author, model, assembly, child_path)
            row["result_update_stamp"] = int(author.get(child, "GetUpdateStamp"))
            row["geometry"] = snapshot(author, model, assembly, expected, child_path, masses, "private child save probe")
            row.update(parent_sha256=digest(parent_path), child_sha256=digest(child_path), completed=True)
        except Exception as error:
            recorder.failure(error)
            row["exception"] = repr(error)
        finally:
            if model is not None:
                try:
                    controller.close_doc(model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if controller is not None:
                controller.close()
                row["controller_diagnostics"] = controller.diagnostics
    if prior is not None:
        row["inputs_immutable"] = parent_path.is_file() and child_path.is_file() and digest(parent_path) == prior["parent_sha256"] and digest(child_path) == prior["child_sha256"]
    row.update(dialogs=monitor.log, progress_windows=monitor.progress)
    row["completed"] = bool(row["completed"] and row.get("inputs_immutable", True) and not row["dialogs"] and not row.get("controller_diagnostics") and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"])
    recorder.data.update(result=row, finished_at=time.time())
    recorder.flush()
    row["record_sha256"] = digest(folder / "Record.json")
    return row


def main():
    job_file = Path(sys.argv[1])
    job = json.loads(job_file.read_bytes())
    AuthorCurves.require(job["schema"] == "kit.sw2026.private-child-save-job.v1", "unexpected child save diagnostic job")
    output, control = (Path(job[key]).resolve() for key in ("output", "control"))
    AuthorCurves.require(not output.is_relative_to(Path(job["checkout_root"]).resolve()) and not control.is_relative_to(output), "child save diagnostic needs isolated output paths")
    raw = control.read_bytes()
    AuthorCurves.require(digest(control) == job["control_sha256"], "child save diagnostic control changed")
    output.mkdir(parents=True, exist_ok=False)
    result = {"schema": "kit.sw2026.private-child-save-probe.v1", "source_revision": job["source_revision"], "tool_sha256": digest(Path(__file__)), "job_sha256": digest(job_file), "started_at": time.time(), "controls": [], "lanes": {}, "native_acceptance": False, "writer_output_count": 0}

    def checkpoint():
        AuthorCurves.write_json(output / "Inspection.json", result)

    def control_phase(kind):
        row = {"kind": kind}
        result["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = bool(healthy(row) and row["oracle_identity"]["sha256"] == job["oracle_sha256"])
        return row

    try:
        start = control_phase("control_before")
        if start["healthy"]:
            for lane in ("silent", "synced"):
                prefix = output / lane
                prefix.mkdir()
                child = prefix / "Child.SLDPRT"
                parent = prefix / "Parent.SLDASM"
                with child.open("xb") as payload:
                    payload.write(raw)
                first = run_phase(job, output, lane, child, parent, start["mass"])
                result["lanes"][lane] = [first]
                checkpoint()
                if first["completed"]:
                    result["lanes"][lane].append(run_phase(job, output, lane, child, parent, start["mass"], first))
                    checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        control_phase("control_after")
        result["controls_healthy"] = len(result["controls"]) == 2 and all(row.get("healthy") for row in result["controls"])
        result["control_immutable"] = digest(control) == job["control_sha256"]
        phases = [row for lane in result["lanes"].values() for row in lane]
        ids = [item["oracle_identity"]["process_creation_filetime"] for item in [*phases, *result["controls"]] if "oracle_identity" in item]
        result["distinct_processes"] = len(set(ids))
        result["diagnostic_completed"] = bool(result["controls_healthy"] and result["control_immutable"] and len(ids) == result["distinct_processes"] == 6 and len(phases) == 4 and all(row["completed"] for row in phases) and not result.get("exception"))
        result["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({key: result[key] for key in ("diagnostic_completed", "controls_healthy", "control_immutable", "distinct_processes")}))
    return 0 if result["diagnostic_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
