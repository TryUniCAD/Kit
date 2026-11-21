from __future__ import annotations

import json
import sys
import time
from pathlib import Path, PureWindowsPath
from shutil import copyfile

from AuthorCurves import EvidenceFailure, Recorder, digest, require, write_json


VARIANTS = ("WithoutPartition", "WithPartition")
MODES = ("StandaloneChild", "DirectParent")
PART = "PartitionProbeChild.SLDPRT"
ASSEMBLY = "L1Single.SLDASM"
NAMES = (ASSEMBLY, PART)
STAGE_NAME = "GeneratedPrismPartition-6c31"
NATIVE_STAGE = PureWindowsPath("C:/Users/Public/Documents/KitOracle") / STAGE_NAME
HELPERS = ("AuthorAssemblySources.py", "AuthorCurves.py", "InspectCircleSketch.py", "InspectFresh.py",
           "ObserveAssemblyLoad.py", "OracleIdentity.py", "ProbeAssemblyRebuild.py", "Swapp.py")


def prepare(job):
    require(job["schema"] == "kit.sw2026.prism-partition-open-diagnostic.v1", "unexpected partition diagnostic job")
    checkout, stage, control = (Path(job[key]).resolve(strict=True) for key in ("checkout_root", "stage", "control"))
    output = Path(job["output"]).resolve()
    require(stage.name == STAGE_NAME and all(not path.is_relative_to(checkout) for path in (stage, control, output)),
            "the exact encoded external assembly stage is required")
    require(digest(control) == job["control_sha256"], "control digest differs")
    active = stage / "Active" / "L1Single"
    copies = stage / "CacheDiagnosticCopies"
    require(not any(path.exists() for path in (active, copies, output)), "partition diagnostic output is already occupied")
    require(set(job["variants"]) == set(VARIANTS), "expected both frozen child variants")
    sources = {}
    for variant in VARIANTS:
        folder = stage / "L1Single" / variant
        require(set(job["variants"][variant]) == set(NAMES), "unexpected variant artifact names")
        sources[variant] = {name: folder / name for name in NAMES}
        for name, source in sources[variant].items():
            require(source.resolve(strict=True).parent == folder and digest(source) == job["variants"][variant][name], "frozen variant digest differs")
    first, second = (job["variants"][name] for name in VARIANTS)
    require(first[ASSEMBLY] == second[ASSEMBLY] and first[PART] != second[PART], "probe requires the same parent and distinct children")
    return active, copies, control, output, sources


def document_state(author, model):
    from ProbeAssemblyRebuild import model_state

    update = int(author.get(model, "GetUpdateStamp"))
    state = model_state(author, model)
    configuration = author.get(author.get(model, "ConfigurationManager"), "ActiveConfiguration")
    return {"update_stamp": update, "configuration": str(author.get(configuration, "Name")), **state}


def face_owner(author, raw):
    try:
        face = author.typed(raw, "Face2")
        feature = author.get(face, "GetFeature")
        if feature is None:
            return None
        return {"name": str(author.get(feature, "Name")), "type": str(author.get(feature, "GetTypeName2"))}
    except Exception as error:
        return {"metadata_error": repr(error)}


def child_state(author, model):
    import Swapp

    before_geometry = document_state(author, model)
    part = author.typed(model, "PartDoc")
    bodies = author.get(part, "GetBodies2", 0, False) or ()
    require(len(bodies) <= 16, "ordinary child diagnostic exceeded its body bound")
    ownership = []
    for raw in bodies:
        body = author.typed(raw, "Body2")
        faces = author.get(body, "GetFaces") or ()
        require(len(faces) <= 64, "ordinary child diagnostic exceeded its face bound")
        ownership.append({"faces": len(faces), "face_owners": [face_owner(author, face) for face in faces]})
    mass = author.rec.call("measure child geometry in system units", Swapp.mass, model) if bodies else None
    return {
        "before_geometry": before_geometry, "after_geometry": document_state(author, model),
        "body_count": len(bodies), "bodies": ownership, "mass": mass,
    }


def observe(author, model, path, mode):
    from AuthorAssemblySources import bound_child

    if mode == MODES[0]:
        return {"child": child_state(author, model)}
    result = {"parent": document_state(author, model)}
    assembly = author.typed(model, "AssemblyDoc")
    try:
        child = bound_child(author, assembly, path, 1)
    except EvidenceFailure as error:
        return result | {"binding_error": str(error)}
    result["child"] = child_state(author, child)
    result["parent_after_child_inspection"] = document_state(author, model)
    return result


def run_phase(job, folder, active, variant, mode):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    area = folder / variant / mode
    area.mkdir(parents=True)
    recorder = Recorder(area / "Record.json", {"variant": variant, "mode": mode})
    row = {"variant": variant, "mode": mode, "completed": False}
    controller = model = None
    source = active / (PART if mode == MODES[0] else ASSEMBLY)
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("fresh oracle idle guard", Swapp.sweep)
            controller = recorder.call("launch owned SOLIDWORKS", Swapp.Sw)
            identity = recorder.call("verify pinned oracle executable", application_identity, controller.app)
            row["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"], "unexpected oracle build")
            author = CurveAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = recorder.call("open the exact encoded diagnostic copy", controller.open, source)
            row["open_status"] = [model is not None, errors, warnings]
            if model is not None and errors == 0:
                row["initial_update_stamp"] = int(author.get(model, "GetUpdateStamp"))
                row["after_open"] = observe(author, model, active / PART, mode)
                row["rebuild_return"] = bool(recorder.call("force rebuild of the open diagnostic copy", author.get, model, "ForceRebuild3", False))
                row["after_rebuild"] = observe(author, model, active / PART, mode)
            row["completed"] = True
        except Exception as error:
            recorder.failure(error)
            row["exception"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if model is not None:
                        recorder.call("close the owned diagnostic document", controller.close_doc, model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                try:
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                row["controller_diagnostics"] = controller.diagnostics
    row.update(dialogs=monitor.log, progress_windows=monitor.progress)
    row["completed"] = bool(row["completed"] and not monitor.log and not row.get("controller_diagnostics")
                            and not recorder.data["cleanup_errors"])
    recorder.data.update(result=row, finished_at=time.time())
    recorder.flush()
    row["record_sha256"] = digest(area / "Record.json")
    return row


def execute(job, job_path, active, copies, control, output, sources):
    from InspectFresh import healthy, inspect

    output.mkdir(parents=True, exist_ok=False)
    copies.mkdir(exist_ok=False)
    report = {
        "schema": "kit.sw2026.prism-partition-open-observations.v1", "job_sha256": digest(job_path),
        "started_at": time.time(), "controls": [], "phases": [], "native_acceptance": False,
        "tool_sha256": {name: digest(Path(__file__).with_name(name)) for name in (Path(__file__).name, *HELPERS)},
    }

    def checkpoint():
        write_json(output / "Inspection.json", report)

    def control_phase(label):
        row = {"kind": label}
        report["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = bool(healthy(row) and row.get("sha256") == job["control_sha256"]
                              and row.get("oracle_identity", {}).get("sha256") == job["oracle_sha256"])
        checkpoint()
        return row["healthy"]

    try:
        if control_phase("before"):
            for variant in VARIANTS:
                active.mkdir(parents=True, exist_ok=False)
                try:
                    for name, source in sources[variant].items():
                        copyfile(source, active / name)
                    for mode in MODES:
                        require(all(digest(active / name) == job["variants"][variant][name] for name in NAMES), "active variant copy changed")
                        report["phases"].append(run_phase(job, output, active, variant, mode))
                        checkpoint()
                    require(all(digest(active / name) == job["variants"][variant][name] for name in NAMES), "observation changed an active copy")
                finally:
                    active.rename(copies / variant)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            control_phase("after")
        except Exception as error:
            report["control_after_exception"] = repr(error)
        report["controls_healthy"] = [row.get("healthy", False) for row in report["controls"]] == [True, True]
        phases = report["phases"]
        states = [row.get("oracle_identity", {}).get("process_creation_filetime") for row in (*report["controls"], *phases)]
        report["distinct_processes"] = len({state for state in states if type(state) is int and state > 0})
        report["inputs_immutable"] = control.is_file() and digest(control) == job["control_sha256"] and all(
            source.is_file() and digest(source) == job["variants"][variant][name] for variant, paths in sources.items() for name, source in paths.items())
        report["diagnostic_completed"] = bool(
            report["controls_healthy"] and report["inputs_immutable"] and not report.get("exception")
            and len(states) == report["distinct_processes"] == 6 and all(row["completed"] for row in phases))
        report["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({key: report[key] for key in ("diagnostic_completed", "controls_healthy", "distinct_processes")}))
    return int(not report["diagnostic_completed"])


if __name__ == "__main__":
    job_path = Path(sys.argv[1]).resolve(strict=True)
    job = json.loads(job_path.read_bytes())
    require(PureWindowsPath(job["stage"]) == NATIVE_STAGE, "native diagnostic uses the originally encoded guest path")
    raise SystemExit(execute(job, job_path, *prepare(job)))
