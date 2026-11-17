from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from shutil import copyfile
import time

from AuthorRectangleAnchors import CONTROL, ORACLE, PARAMETERS, ROLES, RectangleAuthor, control
from AuthorCurves import Recorder, digest, require, write_json


SCHEMA = "kit.sw2026.generated-rectangle-anchor-discovery.v1"
TOOLS = ("AuthorCurves.py", "AuthorRectangleAnchors.py", "InspectFresh.py", "InspectGeneratedRectangleAnchor.py",
         "OracleIdentity.py", "Swapp.py")


def read_job(path, expected):
    require(digest(path) == expected, "rectangle inspection job changed")
    job = json.loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_acceptance"] is False,
            "expected a disclosed anchor comparison against the exact build")
    require(Path(__file__).resolve().parent == path.parent / "Tools" and set(job["tools_sha256"]) == set(TOOLS),
            "expected the complete frozen oracle observer")
    for name, evidence in job["tools_sha256"].items():
        require(digest(path.parent / "Tools" / name) == evidence, f"anchor inspection tool changed: {name}")
    for name, evidence in job["inputs_sha256"].items():
        require(Path(name).name == name and digest(path.parent / name) == evidence, f"anchor input changed: {name}")
    require(set(job["inputs_sha256"]) == {"Control.SLDPRT", "Candidate.SLDPRT", "SourceRecord.json"}
            and job["inputs_sha256"]["Control.SLDPRT"] == CONTROL, "unexpected anchor inspection inputs")
    case = job["case"]
    require(case["kind"] in ("corner", "center") and set(case) == {"kind", "width_m", "height_m", "depth_m", "edit_width_m", "edit_height_m"}
            and all(type(value) in (int, float) and math.isfinite(value) and value > 0.0 for key, value in case.items() if key != "kind")
            and case["width_m"] != case["edit_width_m"] and case["height_m"] != case["edit_height_m"],
            "expected a rectangle anchor with independent width and height perturbations")
    source = json.loads((path.parent / "SourceRecord.json").read_bytes())
    require(source["job"]["case"] == case and source["job"]["phase"] == "Reopen" and source["passed"]
            and source["result"]["oracle_identity"]["sha256"] == ORACLE
            and set(source["result"]["observed"]) == set(ROLES), "independent vendor source receipt does not qualify")
    return job, source["result"]["observed"]


def relation_signature(state):
    return Counter((row["kind"], row["suppressed"], tuple(sorted(row["entity_types"]))) for row in state["relations"])


def construction_edges(state):
    return sorted(tuple(sorted((row["start"], row["end"]))) for row in state["geometry"] if row["construction"])


def compare(rec, state, source):
    actual_edges, source_edges = construction_edges(state), construction_edges(source)
    checks = {
        "ordered_complete_tree": state["tree"] == source["tree"],
        "constraints_and_entity_types": relation_signature(state) == relation_signature(source),
        "body_count": state["body_count"] == source["body_count"],
        "fully_constrained": state["constraint_status"] == source["constraint_status"] == 3,
        "driving_dimension_names": set(state["dimensions_m"]) == set(source["dimensions_m"]),
        "construction_line_count": len(actual_edges) == len(source_edges),
    }
    rec.data["structural_comparison"] = checks
    rec.flush()
    for key, passed in checks.items():
        require(passed, f"native rectangle source parity failed: {key}")
    for actual_line, source_line in zip(actual_edges, source_edges, strict=True):
        for actual_point, source_point in zip(actual_line, source_line, strict=True):
            for actual, expected in zip(actual_point, source_point, strict=True):
                rec.close_number("construction diagonal endpoint", actual, expected)
    for name, value in state["dimensions_m"].items():
        rec.close_number(name, value, source["dimensions_m"][name])
    mass = state["mass_properties"]
    for name in ("volume", "area", "mass"):
        rec.close_number(name, mass[name], source["mass_properties"][name], absolute=1e-16)
    for actual, expected in zip(mass["com"], source["mass_properties"]["com"], strict=True):
        rec.close_number("source center of mass", actual, expected)


def phase(root, name, inputs, case, source, target_states):
    import Swapp
    from OracleIdentity import application_identity

    folder = root / name
    folder.mkdir()
    rec = Recorder(folder / "Record.json", {"name": name, "case": case, "role": tuple(inputs)})
    result = {"passed": False, "states": {}, "files": {}}
    controller, author = None, None
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("verify idle native oracle", Swapp.sweep)
            controller = rec.call("launch fresh anchor oracle", Swapp.Sw)
            identity = rec.call("verify anchor oracle identity", application_identity, controller.app)
            result["oracle_identity"] = identity
            require(identity["sha256"] == ORACLE and identity["version_matches"] and controller.revision == "34.5.2",
                    "native anchor oracle build differs")
            author = RectangleAuthor(controller.app, rec, Swapp)
            for role, (path, expected) in inputs.items():
                require(digest(path) == expected, "native anchor input changed")
                edit = name in ("WidthEdit", "HeightEdit")
                opened = path
                if edit:
                    opened = folder / "Editable.SLDPRT"
                    copyfile(path, opened)
                    require(digest(opened) == expected, "editable native anchor copy changed")
                author.model, errors, warnings = rec.call("open exact anchor input", controller.open, opened, read_only=not edit)
                require(author.model is not None and errors == warnings == 0 and Path(author.get(author.model, "GetPathName")).samefile(opened),
                        f"native anchor open failed or warned: {(errors, warnings)}")
                if edit:
                    parameter, key = (PARAMETERS[0], "edit_width_m") if role == "WidthEdit" else (PARAMETERS[1], "edit_height_m")
                    author.edit(parameter, case[key])
                state = author.snapshot(case, role)
                result["states"][role] = state
                rec.data["result"] = result
                rec.flush()
                compare(rec, state, source[role])
                if name == "Reopen":
                    require(state["tree"] == target_states[role]["tree"] and state["relations"] == target_states[role]["relations"],
                            "native anchor identities changed after editing, saving and reopening")
                if edit:
                    target = folder / "Edited.SLDPRT"
                    status = list(rec.call("save generated anchor edit", controller.save_as, author.model, target))
                    require(status == [True, 0, 0] and target.stat().st_size > 0, "generated anchor edit save failed or warned")
                    result["files"][role] = {"sha256": digest(target), "bytes": target.stat().st_size, "status": status}
                controller.close_doc(author.model)
                author.model = None
                require(digest(path) == expected, "native anchor input changed after inspection")
                rec.flush()
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = dialogs.log
    result["passed"] = bool(result["passed"] and not dialogs.log and not rec.data["cleanup_errors"]
                            and not result.get("controller_diagnostics"))
    rec.data.update(result=result, passed=result["passed"], finished_at=time.time())
    rec.flush()
    return result | {"record_sha256": digest(rec.path)}


def run(path, expected, job, source):
    output = path.parent / "Inspection"
    output.mkdir()
    seed = path.parent / "Control.SLDPRT"
    generated = (path.parent / "Candidate.SLDPRT", job["inputs_sha256"]["Candidate.SLDPRT"])
    report = {"schema": SCHEMA, "job_sha256": expected, "phases": {}, "heldout_acceptance": False, "started_at": time.time()}
    phases = report["phases"]
    report_path = output / "Result.json"
    try:
        phases["ControlBefore"] = control(output, "ControlBefore", seed)
        write_json(report_path, report)
        if phases["ControlBefore"]["passed"]:
            case = job["case"]
            phases["Original"] = phase(output, "Original", {"Original": generated}, case, source, {})
            write_json(report_path, report)
            if phases["Original"]["passed"]:
                for role in ROLES[1:]:
                    phases[role] = phase(output, role, {role: generated}, case, source, {})
                    write_json(report_path, report)
                if all(phases[role]["passed"] for role in ROLES[1:]):
                    saves = {role: (output / role / "Edited.SLDPRT", phases[role]["files"][role]["sha256"]) for role in ROLES[1:]}
                    states = {role: phases[role]["states"][role] for role in ROLES[1:]}
                    phases["Reopen"] = phase(output, "Reopen", saves, case, source, states)
    finally:
        phases["ControlAfter"] = control(output, "ControlAfter", seed)
        report["fresh_processes"] = len({row.get("oracle_identity", {}).get("process_creation_filetime") for row in phases.values()} - {None})
        report["inputs_unchanged"] = all(digest(path.parent / name) == value for name, value in job["inputs_sha256"].items())
        report["passed"] = bool(report["fresh_processes"] == 6 and report["inputs_unchanged"]
                                and all(row["passed"] for row in phases.values()))
        report["finished_at"] = time.time()
        write_json(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Compare a generated anchored rectangle with disclosed native source and edit observations")
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    path = args.job.resolve()
    job, source = read_job(path, args.job_sha256)
    if args.verify_only:
        print(json.dumps({"verified": True, "native_processes": 0}))
        return 0
    result = run(path, args.job_sha256, job, source)
    print(json.dumps({"passed": result["passed"], "fresh_processes": result["fresh_processes"]}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
