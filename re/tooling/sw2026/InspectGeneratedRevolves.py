from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import Swapp
from AuthorCurves import digest, require, write_json
from AuthorRevolveSources import run_phase
from InspectFresh import healthy, inspect


def load_cases(job, checkout):
    cases = []
    names = set()
    for entry in job["cases"]:
        path = Path(entry["source"]).resolve(strict=True)
        require(path.suffix.lower() == ".sldprt" and not path.is_relative_to(checkout), "generated part must be outside the checkout")
        require(path.stem not in names and path.stem == entry["model"]["name"], "duplicate or mismatched candidate name")
        require(digest(path) == entry["sha256"], "generated revolve digest differs before inspection")
        names.add(path.stem)
        cases.append((path, entry))
    require(cases, "at least one generated revolve is required")
    return cases


def main():
    job_path = Path(sys.argv[1]).resolve(strict=True)
    job = json.loads(job_path.read_bytes())
    require(job["schema"] == "kit.sw2026.generated-revolve-inspection-job.v1", "unexpected generated revolve job")
    require(re.fullmatch(r"[0-9a-f]{40}", job["source_revision"]), "generated revolve job requires a pinned source revision")
    handedness = job["forward_handedness"]
    require(type(handedness) is int and handedness in (-1, 1), "generated revolve job requires a signed direction from its native controls")
    inspect_regeneration_warning = job.get("inspect_regeneration_warning", False)
    require(type(inspect_regeneration_warning) is bool, "warning inspection option must be boolean")
    checkout, control, output = (Path(job[key]).resolve() for key in ("checkout_root", "control", "output"))
    require(not output.is_relative_to(checkout), "generated revolve reports must be outside the checkout")
    require(digest(control) == job["control_sha256"], "native control digest differs")
    cases = load_cases(job, checkout)
    output.mkdir(parents=True, exist_ok=False)
    report_path = output / "Inspection.json"
    report = {
        "schema": "kit.sw2026.generated-revolve-inspection.v1",
        "source_revision": job["source_revision"], "oracle_sha256": job["oracle_sha256"],
        "job_sha256": digest(job_path), "inspector_sha256": digest(Path(__file__)),
        "forward_handedness": handedness,
        "inspect_regeneration_warning": inspect_regeneration_warning,
        "started_at": time.time(), "controls": [], "cases": [], "passed": False,
        "heldout_acceptance": False, "saved_edit_reopened": False,
    }

    def control_phase(label):
        row = {"kind": label}
        report["controls"].append(row)
        inspect(control, result=row, checkpoint=lambda: write_json(report_path, report))
        row["healthy"] = bool(healthy(row) and row["sha256"] == job["control_sha256"] and row["oracle_identity"]["sha256"] == job["oracle_sha256"])
        write_json(report_path, report)
        return row["healthy"]

    try:
        if control_phase("control_before"):
            for source, entry in cases:
                Swapp.sweep()
                model = entry["model"]
                row, phase_hash = run_phase(
                    model, "reopen", source, job["oracle_sha256"], entry["sha256"],
                    inspect_regeneration_warning=inspect_regeneration_warning,
                    record_path=output / f"{source.stem}.reopen.json",
                )
                row.update(source_sha256=entry["sha256"], phase_sha256=phase_hash, generator_receipt_sha256=entry["generator_receipt_sha256"])
                initial_direction = None if model["angle_deg"] == 360 else handedness
                edited_direction = None if model["edit_angle_deg"] == 360 else handedness
                direction_matches = (
                    row.get("reopened", {}).get("forward_handedness") == initial_direction
                    and row.get("edited", {}).get("forward_handedness") == edited_direction
                )
                row["direction_matches_signed_target"] = direction_matches
                row["geometry_and_edit_passed"] = bool(row["inspection_completed"] and row.get("edit", {}).get("passed") and direction_matches and not row["cleanup_errors"])
                row["passed"] = row["passed"] and row["geometry_and_edit_passed"]
                report["cases"].append(row)
                write_json(report_path, report)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        control_phase("control_after")
        phases = [*report["controls"], *report["cases"]]
        identities = [row["oracle_identity"]["process_creation_filetime"] for row in phases if "oracle_identity" in row]
        report["distinct_processes"] = len(set(identities))
        report["controls_healthy"] = [row["healthy"] for row in report["controls"]] == [True, True]
        report["passed"] = bool(report["controls_healthy"] and len(identities) == report["distinct_processes"] == 2 + len(cases) and all(row["passed"] for row in report["cases"]) and "exception" not in report)
        report["finished_at"] = time.time()
        write_json(report_path, report)
    print(json.dumps({"passed": report["passed"], "controls_healthy": report["controls_healthy"], "cases": len(report["cases"])}))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
