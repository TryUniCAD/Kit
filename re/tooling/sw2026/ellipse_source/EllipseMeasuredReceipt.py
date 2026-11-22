from hashlib import sha256
from pathlib import Path
import json

from ColdEllipsePacket import neutral_wire
from EllipseModel import require

TRIAL_SHA = "5a0cb6cfe063ac3357e193c5d39ca1749f16ad26ef6e995fdb2cae0ce5244653"
NATIVE_SHA = "6c71cfd01e4b681856a4bd0aaf81d6ef7d2a10af4be1bc4feb4e6bce795d2c93"
BUILD = "34.5.2.0604"
ORACLE_SHA = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"


def digest(raw):
    return sha256(raw).hexdigest()


def load_pin(path, pin):
    raw = path.read_bytes()
    require(digest(raw) == pin, "archived disclosed digest differs at " + path.name)
    return json.loads(raw)


def load_phase(folder, phase):
    slot = phase["slot"]
    key = f"Slot{slot + 1:02}" if slot is not None else Path(phase["control"]).stem
    name = f"{phase['phase']}-{key}.json"
    raw = load_pin(folder / "DisclosedPhases" / name, phase["receipt_sha256"])
    identity = raw["oracle_identity"]
    require(phase["trial_sha256"] == TRIAL_SHA and phase["passed"] and phase["exit_code"] == 0
            and raw["passed"] and not raw["controller_diagnostics"] and not raw["dialogs"]
            and identity["version_matches"] and identity["file_version"] == BUILD and identity["sha256"] == ORACLE_SHA
            and [identity["process_id"], identity["process_creation_filetime"]] == phase["lifetime"],
            "disclosed phase is incomplete or measured on another build")
    if slot is None:
        require(raw["opened"] and raw["rebuilt"] and (raw["open_errors"], raw["open_warnings"], raw["bodies"]) == (0, 0, 1)
                and raw["mass"]["volume"] > 0 and raw["mass"]["area"] > 0,
                "bracket control has no clean native solid measurement")
    else:
        require(raw["job"] == {"phase": phase["phase"], "source_sha256": phase["source"]}
                and raw["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
                and raw["first_failure"] is None and not raw["cleanup_errors"]
                and raw["cold"]["solid_count"] == 1 and raw["cold"]["diagnostics"] == 0
                and len(raw["checks"]) == phase["checks"] and all(check["passed"] for check in raw["checks"]),
                "candidate lacks the recorded clean measured open and checks")
    return raw


def state(stage, sample):
    driver, definition = sample["driver"], sample["definition"]
    body, profile = sample["body"], sample["profile"]
    mass = body["mass"]
    require(driver["value_m"] == definition["depth_m"] and mass["accuracy_level"] == 2
            and profile["contour_closed"] and profile["contour_members"] == 1
            and sample["configurations"] == ["Default"],
            "actual live conic and depth do not match the expected measured owner")
    return {
        "stage": stage, "driver": driver["name"].split("@", 1)[0], "driver_state": driver["state"],
        "readonly": driver["readonly"], "support": profile["support"], "solid_count": body["solid_count"],
        "faces": body["faces"], "tree_rows": len(sample["tree"]), "depth_m": driver["value_m"],
        "volume_m3": mass["volume"], "area_m2": mass["area"], "com_m": mass["com"],
    }


def make_case(slot, request, proof, edit, reopen):
    edit_paths = [row["result"] for row in edit["api_calls"] if row["method"] == "GetPathName"]
    reopened = [row["result"] for row in reopen["api_calls"] if row["method"] == "GetPathName"]
    require(edit_paths == [request["locator"], *reopened] and len(reopened) == 1
            and edit["save_status"] == [True, 0, 0]
            and edit["driver_edit"]["setter_status"] == 0
            and edit["driver_edit"]["requested_m"] == edit["edited"]["driver"]["value_m"]
            and edit["artifact_sha256"] == reopen["job"]["source_sha256"]
            and edit["initial"]["tree"] == edit["edited"]["tree"] == reopen["initial"]["tree"],
            "native final locator, saved derivative or tree identities differ")
    return {
        "slot": slot, "written_at": request["epoch"], "locator": request["locator"],
        "archive_sha256": proof["archive_sha256"], "archive_bytes": proof["bytes"],
        "edited_sha256": reopen["job"]["source_sha256"], "save_status": edit["save_status"],
        "setter_status": edit["driver_edit"]["setter_status"],
        "opens": [[raw["open_status"]["errors"], raw["open_status"]["warnings"]] for raw in (edit, reopen)],
        "states": [state("initial", edit["initial"]), state("edited", edit["edited"]), state("reopen", reopen["initial"])],
    }


def normalize(folder):
    trial = load_pin(folder / "Packet/Trial.json", TRIAL_SHA)
    terminal = load_pin(folder / "DisclosedResult.json", NATIVE_SHA)
    require(trial["native_build"] == terminal["oracle_build"] == BUILD and trial["oracle_sha256"] == terminal["oracle_sha256"] == ORACLE_SHA
            and terminal["trial_sha256"] == TRIAL_SHA and terminal["passed"] and terminal["healthy_controls"]
            and terminal["fresh_processes"] == 8 and terminal["idle_after"] and terminal["heldout_credit"] == 0,
            "wrong native trial, oracle, or custody result")
    records = {(phase["slot"], phase["phase"], phase["control"]): load_phase(folder, phase) for phase in terminal["phases"]}
    require(len(records) == 8 and len({tuple(phase["lifetime"]) for phase in terminal["phases"]}) == 8,
            "native lifetimes are not independently bracketed")
    cases, requests = [], []
    for slot, (case, row, comparison) in enumerate(zip(trial["spec"]["cases"], trial["candidates"], terminal["comparisons"], strict=True)):
        wire = neutral_wire(case, slot)
        request = json.loads(wire)
        proof = row["proof"]
        payload = (folder / "Packet" / row["path"]).read_bytes()
        edit, reopen = (records[(slot, phase, None)] for phase in ("edit", "reopen"))
        require(digest(wire) == proof["input_sha256"] and request["locator"] == proof["locator"]
                and digest(payload) == proof["archive_sha256"] == edit["job"]["source_sha256"]
                and len(payload) == proof["bytes"] and comparison["passed"] and comparison["slot"] == slot
                and comparison["tree_rows"] == 25 and comparison["source_states"] == 3,
                "frozen neutral, native container or source comparison differs")
        cases.append(make_case(slot, request, proof, edit, reopen))
        requests.append(request)
    return {
        "schema": "kit.sw2026.ordinary-full-ellipse-measurement.v1",
        "oracle": {"build": BUILD, "sha256": ORACLE_SHA, "product": "SOLIDWORKS 2026 SP05.2"},
        "trial_sha256": TRIAL_SHA, "native_result_sha256": NATIVE_SHA,
        "fresh_processes": terminal["fresh_processes"], "passed": terminal["passed"],
        "healthy_controls": terminal["healthy_controls"], "phases": terminal["phases"], "cases": cases,
    }, requests
