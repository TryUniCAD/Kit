from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys


SLOTS = ("H01", "H02")
ROLES = ("ControlBefore", "Generated", "Reopen", "ControlAfter")
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SOURCE = "c61560deff9c84addd65db48664ce6a5488ad3eecde9a070c62a215a5541d703"


def require(value):
    if not value:
        raise ValueError("offset plane evidence mismatch")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect(path, expected=None):
    data = path.read_bytes()
    fingerprint = digest(data)
    require(expected is None or fingerprint == expected)
    return json.loads(data), fingerprint


def check_geometry(row):
    expected = row["expected_geometry"]
    actual = row["mass_properties"]
    require(row["body_count"] == expected["body_count"] == 1)
    require(all(math.isclose(a, b, rel_tol=5e-7, abs_tol=1e-12) for a, b in
                zip((actual["volume"], actual["area"], *actual["com"]),
                    (expected["volume"], expected["area"], *expected["com"]), strict=True)))
    require(len(row["feature_tree"]) == 26 and all(node["error"] == 0 and not node["warning"] and
            not node["suppressed"] for node in row["feature_tree"]))


def check_phase(private, row, identity):
    role = row["role"]
    native, fingerprint = inspect(private / "Inspection" / role / "Record.json")
    expected = {key: value for key, value in row.items() if key not in ("role", "started_at", "finished_at")}
    require(native["result"] == expected and native["job"]["role"] == role and native["passed"] is True)
    require(native["job"]["input_sha256"] == identity and native["first_failure"] is None and not native["cleanup_errors"])
    require(row["passed"] is True and row["open_errors"] == row["open_warnings"] == row["initial_needs_rebuild"] == 0)
    require(row["initial_body_count"] == 1 and not row["controller_diagnostics"] and not row["dialogs"])
    require(row["oracle_identity"]["sha256"] == ORACLE and row["oracle_identity"]["version_matches"] is True)
    require(all(check["passed"] is True for check in native["checks"]))
    for name in ("rebuilt", "edited") if role == "Generated" else ("rebuilt",):
        check_geometry(row[name])
    return fingerprint, len(native["checks"]), row["oracle_identity"]["process_creation_filetime"]


def check_slot(root, method_sha, code_sha, private_base, slot):
    progress = root / "Progress" / slot / "T01"
    built, build_record = inspect(progress / "build" / "Record.json")
    accepted, native_record = inspect(progress / "qualify" / "Record.json")
    for stage, phase in ((built, "build"), (accepted, "qualify")):
        require(stage["stage"] == "passed" and stage["passed"] is True and stage["phase"] == phase)
        require(stage["code_lock_sha256"] == method_sha and stage["source_manifest_sha256"] == code_sha and
                stage["source_lock_sha256"] == SOURCE and stage["slot"] == slot)
    require(built["finished_at"] <= accepted["started_at"])
    private = private_base / slot / "T01"
    job, job_sha = inspect(private / "PairedTrial.json", built["private_observation_sha256"])
    frozen, freeze_sha = inspect(private / "GenerationFreeze.json", built["build_manifest_sha256"])
    require(job["slot"] == slot and job["mode"] == "heldout" and job["generation_freeze_sha256"] == freeze_sha)
    require(job["heldout_inputs_read"] == 1 and job["host_private_payloads_read"] == 0 and
            job["code_manifest_sha256"] == frozen["code_manifest_sha256"] == code_sha)
    require(frozen["guarded_builds"] == 2 and frozen["runtime_input_reads"] == frozen["native_sources_read"] == 0)
    require(job["generated"]["sha256"] == frozen["generated_sha256"])
    for role, folder in (("control", "Controls"), ("generated", "FrozenGenerated"), ("generated", "GeneratedInput")):
        entry = job[role]
        require(Path(entry["filename"]).name == entry["filename"])
        require(digest((private / folder / entry["filename"]).read_bytes()) == entry["sha256"])
    custody, custody_sha = inspect(private / "OriginalCustody.json")
    require(custody["source"]["sha256"] == job["control"]["sha256"])
    require(all(digest(Path(row["path"]).read_bytes()) == row["sha256"] for row in custody.values()))
    result, result_sha = inspect(private / "Inspection" / "PairedReferencePlaneResults.json", accepted["private_observation_sha256"])
    require(result["packet_sha256"] == job_sha and result["heldout_inputs_read"] == 1 and result["distinct_processes"] == 4)
    require(all(result[name] is True for name in ("passed", "controls_healthy", "immutable_inputs_unchanged",
                "native_phases_distinct_and_ordered", "source_generated_paired_acceptance", "generated_initial_edit_tree_equal",
                "generated_edit_reopen_tree_equal")))
    require(all(result[name]["passed"] is True and len(result[name]["checks"]) == 10 and
                all(result[name]["checks"].values()) for name in ("source_generated_identity", "source_bracket_identity")))
    require(tuple(row["role"] for row in result["phases"]) == ROLES)
    edited = result["phases"][1]
    saved = edited["saved"]
    require(edited["edit_status"] == 0 and saved["status"] == [True, 0, 0] and
            Path(saved["filename"]).name == saved["filename"])
    require(digest((private / "Saved" / saved["filename"]).read_bytes()) == saved["sha256"])
    identities = (job["control"]["sha256"], job["generated"]["sha256"], saved["sha256"], job["control"]["sha256"])
    rows = [check_phase(private, row, identity) for row, identity in zip(result["phases"], identities, strict=True)]
    require(sum(row[1] for row in rows) == 81)
    births = {row[2] for row in rows}
    require(len(births) == 4 and all(type(value) is int and value > 0 for value in births))
    return {"slot": slot, "build_record_sha256": build_record, "native_record_sha256": native_record,
            "packet_sha256": job_sha, "freeze_sha256": freeze_sha, "custody_sha256": custody_sha,
            "private_observation_sha256": result_sha, "phase_sha256": dict(zip(ROLES, (row[0] for row in rows), strict=True)),
            "saved_sha256": saved["sha256"], "generated_sha256": job["generated"]["sha256"], "passed": True}, births


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--method-sha256", required=True)
    args = parser.parse_args()
    if os.name != "nt":
        print(json.dumps({"passed": False, "failure_code": "windows_guest_required"}))
        return 1
    try:
        method, method_sha = inspect(args.root / "Method.json", args.method_sha256)
        recipe, _ = inspect(args.root / "Recipe.json", method["recipe_sha256"])
        require(method["source_lock_sha256"] == recipe["source"]["source_lock_sha256"] == SOURCE)
        private_base = Path(recipe["guest_private_base"])
        require(private_base.is_absolute() and re.fullmatch(r"[A-Za-z]:", private_base.drive) and ".." not in private_base.parts)
        collected = [check_slot(args.root, method_sha, method["code_manifest_sha256"], private_base, slot) for slot in SLOTS]
        require(len(set.union(*(births for _, births in collected))) == 8)
        print(json.dumps({"schema": "kit.sw2026.offset-plane-original-audit.v1", "method_sha256": method_sha,
                          "source_lock_sha256": SOURCE, "code_manifest_sha256": method["code_manifest_sha256"],
                          "slots": [report for report, _ in collected], "passed": True}, sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({"passed": False, "failure_code": "guest_record_audit_failed"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
