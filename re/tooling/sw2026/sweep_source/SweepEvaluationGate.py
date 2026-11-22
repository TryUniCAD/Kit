from hashlib import sha256
import json

from RunSweepCold import PHASES
from RunSweepSources import CONTROLS, PROCESS_COUNT
from SweepColdPacket import API, LOCK, SEALED_LOCK, SOURCE_LOCK
from SweepModel import require
from SweepPacket import BUILD, CONTROL, ORACLE, digest, valid_hash


DISCLOSED_JOB = "b2afe3deb3f41eb7676c82fe50f289cb0f01863a64b15707fe8099fcb3ba1055"
DISCLOSED_RESULT = "380ead8ff07a9337bd0df87d32eb92e49529e0579c15449767a5ee26e53dd512"
WRITER = "09b77272b02b74a1b4d54413cc185cb602105527"
SDK_TREE = "392993e1c5f530d854c132482b268d1554d8c5c7"
PREWRITER_PATH = "re/solidworks/measurements/2026/OrdinarySweptBossPrewriterLock01.json"
SLOTS = ("Slot01", "Slot02")
ROLES = ("original", "section", "path")


def prewriter(raw):
    lock = json.loads(raw)
    require(lock["schema"] == "kit.sw2026.standard-sweep-prewriter-lock.v1"
            and (lock["source_lock_sha256"], lock["disclosed_lock_sha256"], lock["registered_api_sha256"])
            == (SEALED_LOCK, SOURCE_LOCK, API) and (lock["oracle_build"], lock["oracle_sha256"]) == (BUILD, ORACLE)
            and lock["distinct_native_processes"] == PROCESS_COUNT and lock["writer_output_count"] == 0
            and lock["heldout_writer_acceptance"] is False and tuple(row["slot"] for row in lock["slots"]) == SLOTS
            and all(valid_hash(lock[key]) for key in ("source_job_sha256", "spec_sha256", "prediction_sha256"))
            and set(lock["controls"]) == {"before", "after"} and all(map(valid_hash, lock["controls"].values())),
            "wrong original pre-writer sweep lock")
    for row in lock["slots"]:
        require(set(row["artifact_sha256"]) == set(ROLES) and all(map(valid_hash, row["artifact_sha256"].values()))
                and len(row["phase_receipt_sha256"]) == len(PHASES)
                and all(map(valid_hash, row["phase_receipt_sha256"])), "pre-writer source phase is unbound")
    return lock


def phase_ok(row, pin, phase, slot):
    return ((row["phase"], row["job_sha256"], row["slot"]) == (phase, pin, slot) and row["passed"] is True
            and row["worker_exit_code"] == 0 and row["timed_out"] is False and valid_hash(row["receipt_sha256"]))


def verify_result(result, job, pin, comparison):
    require(result["schema"] == "kit.sw2026.standard-sweep-cold-result.v1" and result["job_sha256"] == pin
            and (result["oracle_build"], result["oracle_sha256"], result["writer_revision"]) == (BUILD, ORACLE, WRITER)
            and result["source_lock_sha256"] == job["source_lock_sha256"] == comparison["source_lock_sha256"]
            and result["passed"] is result["idle_after"] is result["inputs_unchanged"] is True
            and result["distinct_processes"] == result["started_processes"] == PROCESS_COUNT
            and result["heldout_credit"] == 0 and len(result["cases"]) == len(comparison["cases"]) == len(SLOTS)
            and set(result["controls"]) == {"before", "after"}, "required native sweep batch did not completely pass")
    for role, phase in zip(("before", "after"), CONTROLS, strict=True):
        control = result["controls"][role]
        require(phase_ok(control, pin, phase, None) and control["source_sha256"] is None,
                "native sweep bracket control failed")
    for slot, (case, expected, relative) in enumerate(zip(result["cases"], comparison["cases"], sorted(job["candidates"]), strict=True)):
        require(case["slot"] == expected["slot"] == slot and case["passed"] is True
                and case["independent_source_sha256"] == expected["native_source_sha256"]
                and case["independent_observer_sha256"] == expected["source_receipt_sha256"]
                and case["paired_numeric_checks"] == 84 and len(case["phases"]) == len(PHASES),
                "native sweep comparison or source pairing is incomplete")
        artifacts = case["candidate_sha256"]
        require(set(artifacts) == set(ROLES) and artifacts["original"] == job["files"][relative]["sha256"]
                and all(map(valid_hash, artifacts.values())) and len(set(artifacts.values())) == len(ROLES),
                "native terminal is not bound to its generated candidate and both edits")
        for phase, row in zip(PHASES, case["phases"], strict=True):
            role, _, action = phase.partition("-")
            incoming = role if action == "reopen" else "original"
            output = role if role in ROLES else "original"
            require(phase_ok(row, pin, phase, slot) and row["checks"] == row["checks_passed"] > 0
                    and row["source_sha256"] == artifacts[incoming] and row["artifact_sha256"] == artifacts[output],
                    "native candidate phase did not retain exact code, checks and artifact lineage")


def verified_file(path, expected):
    require(valid_hash(expected) and path.is_file() and not path.is_symlink() and path.resolve() == path,
            "expected a canonical immutable file")
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected, "immutable sweep evidence digest differs")
    return raw


def check_native_controls(result, packet, capture):
    from SealSweepSources import pinned_json
    from InspectFresh import healthy

    require(digest(packet / "Control.SLDPRT") == CONTROL, "native control input differs")
    processes = set()
    for row in result["controls"].values():
        record = pinned_json(capture / row["phase"] / "Record.json", row["receipt_sha256"])
        require(record["passed"] is True and record["sha256"] == CONTROL and healthy(record),
                "native control payload is unhealthy")
        processes.add(exact_process(record))
    return processes


def exact_process(record):
    identity = record["oracle_identity"]
    require((identity["file_version"], identity["sha256"], identity["pe_machine"]) == (BUILD, ORACLE, "0x8664")
            and identity["version_matches"] is True, "native phase ran under another build")
    return identity["process_id"], identity["process_creation_filetime"]
