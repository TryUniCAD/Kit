from __future__ import annotations

import json
from math import isclose
from pathlib import Path
from shutil import copytree
import sys
import time

import Swapp
from AuthorCurves import digest, require, write_json
from AuthorRevolveEnds import RevolveEndAuthor, read_constants, validate_cases
from AuthorRevolveSources import run_phase
from InspectFresh import healthy, inspect


def compare_state(actual, source):
    require(actual["bodies"] == source["bodies"] == 1, "solid body count differs")
    for label in ("api_mode", "reverse", "parents", "forward_handedness"):
        require(actual[label] == source[label], "native feature differs in " + label)
    for value, expected in zip(actual["angles_radians"], source["angles_radians"], strict=True):
        require(isclose(value, expected, rel_tol=1e-13, abs_tol=1e-14), "native angular slot differs")
    for point, expected in zip(actual["axis"]["points"], source["axis"]["points"], strict=True):
        require(all(isclose(left, right, abs_tol=1e-12, rel_tol=0) for left, right in zip(point, expected, strict=True)), "selected native axis differs")
    fields = ("name", "type", "error", "warning", "suppressed")
    actual_tree = [tuple(row[key] for key in fields) for row in actual["features"]]
    source_tree = [tuple(row[key] for key in fields) for row in source["features"]]
    require(actual_tree == source_tree, "native ordered feature tree differs")
    for key in ("volume", "area", "mass"):
        require(format(actual["mass"][key], ".6g") == format(source["mass"][key], ".6g"), "native property differs in " + key)
    for value, expected in zip(actual["mass"]["com"], source["mass"]["com"], strict=True):
        require(abs(value) <= 1e-12 and abs(expected) <= 1e-12 or format(value, ".6g") == format(expected, ".6g"), "native centre of mass differs")
    return {"tree_rows": len(actual_tree), "mass_checks": 6, "actual": actual["mass"], "source": source["mass"]}


def compare_edits(actual, source):
    a, b = (value["edit"]["dimensions"] for value in (actual, source))
    require(len(a) == len(b), "native active angular driver count differs")
    for left, right in zip(a, b, strict=True):
        require(left["name"].split("@")[:2] == right["name"].split("@")[:2], "native angular driver name differs")
        require(left["setter_status"] == right["setter_status"] == 0, "native angular driver did not edit")
        for key in ("before_radians", "after_radians"):
            require(isclose(left[key], right[key], rel_tol=1e-13), "native edit value differs")


def run_candidate(case, files, directory, oracle):
    name = case["name"]
    directory.mkdir()
    path = Path(files["candidate"])
    known = files["candidate_sha256"]
    references = []
    for key in ("original", "edited"):
        source = Path(files[key])
        require(digest(source) == files[key + "_sha256"], "disclosed native reference receipt changed")
        receipt = json.loads(source.read_bytes())
        require(receipt["passed"] and receipt["source_immutable"], "disclosed native reference receipt is incomplete")
        references.append(receipt)
    edited_path = directory / (name + "-edited.SLDPRT")
    first, r1 = run_phase(case, "reopen", path, oracle, known, inspect_before_rebuild=True, inspect_profile=True,
                          record_path=directory / "Initial.json", save_edited=edited_path, author_type=RevolveEndAuthor)
    rows = [first]
    result = {"name": name, "candidate_sha256": known, "native_phase_sha256": [r1], "passed": False, "comparisons": {}}
    if first["passed"] and first.get("edit", {}).get("passed"):
        edited = dict(case, angle_deg=case["edit_angle_deg"], second_deg=case["edit_second_deg"])
        second, r2 = run_phase(edited, "edited-reopen", edited_path, oracle, first["edited_derivative"]["sha256"],
                               inspect_before_rebuild=True, inspect_profile=True, record_path=directory / "FreshReopen.json",
                               author_type=RevolveEndAuthor)
        rows.append(second)
        result["native_phase_sha256"].append(r2)
    try:
        for row in rows:
            require(row["passed"], "native candidate phase did not complete")
            require(row["open_status"] == {"opened": True, "errors": 0, "warnings": 0}, "native open reports a warning or error")
            require(row["before_explicit_rebuild"]["bodies"] == 1, "cold open lacks one solid body")
        require(len(rows) == 2 and digest(path) == known, "generated source changed or edited reopen did not run")
        compare_edits(first, references[0])
        for key in ("reopened", "after-d1", "edited"):
            if key in references[0]:
                result["comparisons"][key] = compare_state(first[key], references[0][key])
        result["comparisons"]["edited_fresh_reopen"] = compare_state(rows[1]["reopened"], references[1]["reopened"])
        result["passed"] = True
    except (ValueError, RuntimeError, AssertionError, KeyError) as error:
        result["first_failure"] = str(error)
    result["native_phase_failures"] = [row["first_failure"] for row in rows]
    return result, rows


def main():
    path = Path(sys.argv[1])
    job = json.loads(path.read_bytes())
    require(job["schema"] == "kit.sw2026.generated-ordinary-revolve-ends.v1", "invalid generated evaluation job")
    spec_path, output, publication, control = (Path(job[name]) for name in ("spec", "output", "publication", "control"))
    require(digest(spec_path) == job["spec_sha256"] and digest(control) == job["control_sha256"], "immutable native batch input changed")
    require(not output.exists() and not publication.exists(), "evaluation destinations must be fresh")
    spec = json.loads(spec_path.read_bytes())
    require(spec["split"] == "discovery", "this evaluation uses disclosed references")
    cases = validate_cases(spec)
    RevolveEndAuthor.constants = read_constants()
    output.mkdir(parents=True)
    oracle = job["oracle_sha256"]
    outcome = {"schema": "kit.sw2026.generated-ordinary-revolve-disclosure.v1", "writer_revision": job["writer_revision"],
               "writer_source_tree": job["writer_source_tree"], "generation_receipt_sha256": job["generation_receipt_sha256"],
               "oracle_sha256": oracle, "build": "34.5.2.0604", "job_sha256": digest(path),
               "spec_sha256": job["spec_sha256"], "started_at": time.time(), "cases": [], "heldout_writer_acceptance": False}
    ids = []

    def measure_control(label):
        info = inspect(control)
        result_path = output / (label + ".json")
        write_json(result_path, info)
        if "oracle_identity" in info:
            ids.append(info["oracle_identity"]["process_creation_filetime"])
        outcome[label] = {"sha256": digest(result_path), "passed": healthy(info)
                          and info["sha256"] == job["control_sha256"] and info["oracle_identity"]["sha256"] == oracle}

    try:
        measure_control("control-before")
        if outcome["control-before"]["passed"]:
            for case in cases:
                result, rows = run_candidate(case, job["files"][case["name"]], output / case["name"], oracle)
                outcome["cases"].append(result)
                ids.extend(row["oracle_identity"]["process_creation_filetime"] for row in rows if "oracle_identity" in row)
    except Exception as error:
        outcome["batch_failure"] = repr(error)
    finally:
        measure_control("control-after")
    outcome.update(finished_at=time.time(), distinct_processes=len(set(ids)),
                   application_idle=not Swapp.application_pids() and not Swapp.owned_process_ids(),
                   controls_unchanged=digest(control) == job["control_sha256"])
    outcome["passed"] = bool(outcome.get("control-before", {}).get("passed") and outcome["control-after"]["passed"]
                             and outcome["application_idle"] and outcome["controls_unchanged"] and not outcome.get("batch_failure")
                             and len(outcome["cases"]) == len(cases) and len(ids) == outcome["distinct_processes"] == 2 + 2 * len(cases)
                             and all(row["passed"] for row in outcome["cases"]))
    write_json(output / "NativeReceipt.json", outcome)
    copytree(output, publication)
    Swapp.emit({"passed": outcome["passed"], "candidates": len(outcome["cases"]), "distinct_processes": outcome["distinct_processes"]})
    return int(not outcome["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
