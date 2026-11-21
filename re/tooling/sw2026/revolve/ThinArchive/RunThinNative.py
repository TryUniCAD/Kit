from pathlib import Path
import json
import os
import sys
import time

from AuthorRevolveFamilies import ORACLE, author_type, constants_from_registration, digest
from CompareThinNative import compare_cycle
from RevolveFamilyModel import edited_case, need, validate_specs

SCHEMA = "kit.sw2026.generated-thin-disclosure-job.v1"
PLANE_SCHEMA = "kit.sw2026.generated-thin-principal-disclosure-job.v1"
VERSION = "34.5.2.0604"


def check_paths(root, files):
    for name, expected in files.items():
        candidate = (root / name).resolve(strict=True)
        need(candidate.is_relative_to(root) and candidate.is_file() and digest(candidate) == expected,
             "staged disclosed native input or tool digest differs")


def check_phase(row, expected_roles=None):
    initial = row["before_explicit_rebuild"]
    need(row["passed"] and row["source_immutable"] and row["inspection_completed"]
         and row["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
         and initial["bodies"] == 1 and initial["whats_wrong"] == 0,
         "native phase did not cleanly open one cold body and complete rebuild")
    if expected_roles is not None:
        need(row["edit"]["passed"] and tuple(item["role"] for item in row["edit"]["dimensions"]) == expected_roles
             and row["edited_derivative"]["save_status"] == [True, 0, 0], "native driver edits or derivative save failed")


def run_lane(case, path, known, output, author, run_phase, record_process, idle):
    output.mkdir(parents=True)
    derivative = output / (case["name"] + "-edited.SLDPRT")
    rows, receipts = [], []
    next_step = (case, "reopen", path, known)
    for label in ("Initial", "FreshReopen"):
        want_case, phase, asset, sha = next_step
        need(idle(), "native application remained active between distinct phases")
        row, receipt = run_phase(want_case, phase, asset, ORACLE, sha,
                                 inspect_before_rebuild=True, record_path=output / (label + ".json"),
                                 save_edited=derivative if phase == "reopen" else None, author_type=author)
        rows.append(row)
        record_process(row)
        receipts.append({"phase": phase, "sha256": receipt, "passed": row["passed"],
                         "open_status": row.get("open_status"), "first_failure": row.get("first_failure"),
                         "cold_bodies": row.get("before_explicit_rebuild", {}).get("bodies"),
                         "checks": len(row["checks"]), "checks_passed": sum(m["passed"] for m in row["checks"])})
        if phase == "reopen":
            if not row["passed"] or not row.get("edit", {}).get("passed") or "edited_derivative" not in row:
                break
            next_step = (edited_case(case), "edited-reopen", derivative, row["edited_derivative"]["sha256"])
    return rows, receipts


def evaluate_case(root, case, output, files, runner):
    name = case["name"]
    summary = {"case": name, "passed": False, "native_phases": {}, "comparisons": {}}
    observed = {}
    for label, folder in (("source", "Sources"), ("candidate", "Candidates")):
        source_name = f"{folder}/{name}.SLDPRT"
        sha = files[source_name]
        summary[label + "_sha256"] = sha
        rows, receipts = runner(case, root / source_name, sha, output / name / label)
        observed[label], summary["native_phases"][label] = rows, receipts
    try:
        roles = ("angle", "wall1", "wall2") if case["wall_mode"] == "two" else ("angle", "wall1")
        for rows in observed.values():
            need(len(rows) == 2, "native edit/save/reopen chain was incomplete")
            check_phase(rows[0], roles)
            check_phase(rows[1])
        original = json.loads((root / f"References/{name}.reopen.json").read_bytes())
        derivative = json.loads((root / f"References/{name}-edited.edited-reopen.json").read_bytes())
        summary["comparisons"]["source_to_prior_native"] = compare_cycle(observed["source"], (original, derivative), case["wall_mode"])
        summary["comparisons"]["candidate_to_current_source"] = compare_cycle(observed["candidate"], observed["source"], case["wall_mode"])
    except (ValueError, RuntimeError, KeyError, TypeError) as error:
        summary["refusal"] = str(error)
    else:
        summary["passed"] = True
    return summary


def execute(job_path, job_sha):
    need(os.name == "nt" and sys.version_info[:2] == (3, 12), "this disclosed runner requires the designated Windows 3.12 guest")
    import Swapp
    from functools import partial
    from AuthorCurves import write_json
    from AuthorRevolveSources import PLANES, RevolveAuthor, run_phase
    from InspectFresh import healthy, inspect

    job_path = job_path.resolve(strict=True)
    root = job_path.parent
    need(digest(job_path) == job_sha and Path(__file__).resolve().parent.parent == root and root.drive.casefold() == "c:",
         "native job or executable packet location differs")
    job = json.loads(job_path.read_bytes())
    schema = job["schema"]
    need(schema in (SCHEMA, PLANE_SCHEMA) and job["oracle_sha256"] == ORACLE and Path(job["logical_root"]) == root,
         "wrong frozen native runner job or logical root")
    check_paths(root, job["files"])
    plan = json.loads((root / "ModelSpec.json").read_bytes())
    cases = validate_specs(plan)
    need(plan["split"] == "discovery" and plan["family"] == "thin",
         "native batch requires disclosed thin controls")
    if schema == SCHEMA:
        need(len(cases) == 4, "native batch requires the four disclosed Front controls")
    else:
        need(tuple((case["plane"], case["wall_mode"], case["reverse"]) for case in cases)
             == (("top", "opposite", False), ("right", "midplane", False)),
             "native batch requires the two exact principal-plane contrast roles")
    output = root / "Oracle"
    need(not output.exists(), "native evidence destination already exists")

    def idle():
        return not Swapp.application_pids() and not Swapp.owned_process_ids()

    need(idle(), "native application is already active")
    constants = constants_from_registration(Swapp)
    author = author_type(RevolveAuthor, PLANES, Swapp, constants)
    output.mkdir()
    processes = []
    result_schema = ("kit.sw2026.thin-generated-disclosure-result.v1" if schema == SCHEMA
                     else "kit.sw2026.thin-principal-disclosure-result.v1")
    summary = {"schema": result_schema, "job_sha256": job_sha,
               "oracle_sha256": ORACLE, "oracle_build": VERSION, "writer_revision": job["writer_revision"],
               "writer_sdk_tree": job["writer_sdk_tree"], "build_receipt_sha256": job["files"]["BuildReceipt.json"],
               "source_lock_sha256": job["source_lock_sha256"], "heldout_writer_acceptance": False,
               "registered_swconst": constants, "cases": [], "started_at": time.time()}

    def record_process(row):
        if "oracle_identity" in row:
            native = row["oracle_identity"]
            need(native["sha256"] == ORACLE and native["file_version"] == VERSION,
                 "native process does not match the configured oracle")
            processes.append(native["process_creation_filetime"])

    def control(label):
        need(idle(), "native application remained active before a bracket control")
        path = root / "Control.SLDPRT"
        row = inspect(path)
        report = output / (label + ".json")
        write_json(report, row)
        record_process(row)
        summary[label] = {"sha256": digest(report), "passed": healthy(row) and row["sha256"] == job["files"][path.name]}

    try:
        control("control-before")
        if summary["control-before"]["passed"]:
            runner = partial(run_lane, author=author, run_phase=run_phase, record_process=record_process, idle=idle)
            for case in cases:
                summary["cases"].append(evaluate_case(root, case, output, job["files"], runner))
    except Exception as error:
        summary["batch_failure"] = type(error).__name__ + ": " + str(error)
    finally:
        try:
            control("control-after")
        except Exception as error:
            summary["control-after"] = {"passed": False, "failure": type(error).__name__ + ": " + str(error)}
    summary.update(fresh_processes=len(processes), distinct_processes=len(set(processes)), idle_after=idle(), finished_at=time.time())
    try:
        check_paths(root, job["files"])
        summary["inputs_unchanged"] = digest(job_path) == job_sha
    except (ValueError, OSError):
        summary["inputs_unchanged"] = False
    summary["passed"] = (not summary.get("batch_failure") and summary.get("control-before", {}).get("passed", False)
                         and summary["control-after"]["passed"] and summary["inputs_unchanged"] and summary["idle_after"]
                         and summary["fresh_processes"] == summary["distinct_processes"] == 2 + 4 * len(cases)
                         and len(summary["cases"]) == len(cases) and all(item["passed"] for item in summary["cases"]))
    result = output / "NativeResult.json"
    write_json(result, summary)
    Swapp.emit({"passed": summary["passed"], "cases": len(summary["cases"]), "result_sha256": digest(result)})
    return int(not summary["passed"])


if __name__ == "__main__":
    raise SystemExit(execute(Path(sys.argv[1]), sys.argv[2]))
