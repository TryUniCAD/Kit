from hashlib import sha256
import json

from EllipseModel import CASES, require

SOURCE_LOCK = "1ecae416cf69cc532072418ec56a55df62c3abe2e638851ea41777352e736fd5"
BUILD = "34.5.2.0604"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
PHASES = ("author", "reopen-edit-save", "edited-reopen")
STATES = (("authored", "reopened"), ("edited", "reopened"))
CODEC_BASELINE = "b2036eae24408422fb98ac2c949f8389d156b165"
SERIALIZE_MAP = "dbb788346ee44610cb365a44e6150a8264b03f93fed9832a19caa8ad24dabec4"
MODEL_MODULE = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"


def digest(value):
    return sha256(value).hexdigest()


def pinned(path, expected):
    raw = path.read_bytes()
    require(digest(raw) == expected, f"disclosed SHA-256 differs for {path.name}")
    return raw


def read_phase(folder, lock, row, phase, slot, original, edited):
    phase_id = phase["phase"]
    incoming = {"author": None, "reopen-edit-save": original, "edited-reopen": edited}[phase_id]
    artifact = original if phase_id == "author" else edited
    receipt = json.loads(pinned(folder / f"Slot{slot + 1:02d}-{phase_id}.json", phase["phase_sha256"]))
    identity = receipt["oracle_identity"]
    require(phase["passed"] and phase["slot"] == row["slot"] == slot
            and phase["exit_code"] == 0 and phase["job_sha256"] == lock["job_sha256"]
            and phase["source_sha256"] == incoming and phase["artifact_sha256"] == artifact
            and len(receipt["checks"]) == phase["checks"]
            and receipt["passed"] and receipt["source_immutable"] and receipt["writer_output_count"] == 0
            and receipt["artifact_sha256"] == artifact and receipt["first_failure"] is None
            and not receipt["cleanup_errors"] and not receipt["dialogs"]
            and receipt["job"] == {"phase": phase_id, "source_sha256": incoming}
            and identity["file_version"] == BUILD and identity["sha256"] == ORACLE
            and identity["version_matches"] and identity["pe_machine"] == "0x8664",
            "disclosed ellipse phase differs from the successful native lock")
    if incoming is not None:
        require(receipt["open_status"] == {"opened": True, "errors": 0, "warnings": 0},
                "disclosed ellipse was not opened cleanly")
    if phase_id != "edited-reopen":
        require(receipt["save_status"] == [True, 0, 0], "disclosed ellipse was not saved cleanly")
    return receipt


def load_disclosed(folder):
    lock = json.loads(pinned(folder / "SourceLock.json", SOURCE_LOCK))
    registered = json.loads(pinned(folder / "RegisteredApi.json", lock["registered_api_sha256"]))
    require(lock["cohort"] == "disclosed" and lock["passed"] and lock["oracle_build"] == BUILD
            and lock["oracle_sha256"] == ORACLE and lock["idle_after"] and lock["inputs_unchanged"]
            and not lock["heldout_writer_acceptance"] and lock["writer_output_count"] == 0
            and lock["fresh_processes"] == lock["distinct_processes"] == 10
            and set(lock["controls"]) == {f"control-{side}-{case}" for side in ("before", "after")
                                          for case in ("ControlCircle", "ControlRectangle")}
            and all(control["passed"] and control["exit_code"] == 0
                    for control in lock["controls"].values()),
            "ellipse source lock is outside the healthy disclosed acquisition")
    cases, processes = [], set()
    for slot, (case, row) in enumerate(zip(CASES, lock["sources"], strict=True)):
        original, edited = row["original_sha256"], row["edited_sha256"]
        require(row["passed"] and row["snapshots"] == 4 and original != edited
                and tuple(phase["phase"] for phase in row["phases"]) == PHASES,
                "disclosed ellipse lifecycle is incomplete")
        receipts = [read_phase(folder, lock, row, phase, slot, original, edited) for phase in row["phases"]]
        for receipt in receipts:
            identity = receipt["oracle_identity"]
            processes.add((identity["process_id"], identity["process_creation_filetime"]))
        for is_edit, state_pair in enumerate(STATES):
            name = case["name"] + ("Edited" if is_edit else "")
            pin = edited if is_edit else original
            raw = pinned(folder / (name + ".SLDPRT"), pin)
            two_receipts = receipts[1:] if is_edit else receipts[:2]
            rim = (receipts[2] if is_edit else receipts[0])["last_rim_trim"]
            observations = [receipt[k] for receipt, k in zip(two_receipts, state_pair, strict=True)]
            cases.append({"case": name, "slot": slot, "edited": bool(is_edit), "sha256": pin,
                          "raw": raw, "observations": observations, "rim": rim,
                          "observation_pins": [phase["phase_sha256"]
                                               for phase in (row["phases"][1:] if is_edit else row["phases"][:2])]})
    require(len(processes) == 6 and len({row["sha256"] for row in cases}) == 4,
            "ellipse observations or archives alias separate phases")
    return lock, registered, cases
