import json
from pathlib import Path, PureWindowsPath

from AuditSweepSketches import EPOCH
from ProveSdkSweepPart import NATIVE, ROOT, checked_json
from RunSweepCold import PHASES, members
from RunSweepSources import driver_identity, stable_owners, topology_signature
from SweepColdCompare import compare_source
from SweepColdPacket import verify
from SweepModel import PATH, SECTION, require
from SweepPacket import BUILD, ORACLE, digest


JOB = "b2afe3deb3f41eb7676c82fe50f289cb0f01863a64b15707fe8099fcb3ba1055"
PORTABLE = "b52e938c78eafb58d7da376ee979dbdd630a57159d3ac587e8215690beb5741f"
PORTABLE_FILE = ROOT / "re/solidworks/measurements/2026/SdkPortableSweepDoc01.json"


def record_for(folder, phase, job):
    record = checked_json(folder / "Record.json", phase["receipt_sha256"])
    auth = {key: phase[key] for key in ("phase", "slot", "source_sha256", "job_sha256")}
    require(json.loads((folder / "Phase.json").read_bytes()) == auth
            and auth["job_sha256"] == JOB and phase["passed"] is True
            and not phase["timed_out"] and phase["worker_exit_code"] == 0
            and phase["checks"] == phase["checks_passed"]
            and record["passed"] is True and not record["controller_diagnostics"]
            and not record["dialogs"], "unhealthy or unbound native lifetime")
    identity = record["oracle_identity"]
    require(identity["file_version"] == job["oracle_build"] == BUILD
            and identity["sha256"] == job["oracle_sha256"] == ORACLE
            and identity["version_matches"] is True, "native phase used another oracle")
    row = {key: phase[key] for key in ("phase", "slot", "passed", "checks", "receipt_sha256")}
    row.update(trial_sha256=JOB, exit_code=phase["worker_exit_code"],
               lifetime=[identity["process_id"], identity["process_creation_filetime"]])
    return record, row


def read_control(folder, phase, job, loc, expected_hash):
    record, row = record_for(folder, phase, job)
    require(row["slot"] is None and phase["source_sha256"] is None
            and record["path"] == loc and record["sha256"] == expected_hash
            and record["opened"] is True and record["rebuilt"] is True
            and record["open_errors"] == record["open_warnings"] == record["whats_wrong"] == 0
            and record["bodies"] == 1 and record["stage"] == "close_return",
            "invalid clean bracket control")
    row.update(source=expected_hash, result=expected_hash, open_status=[0, 0], rebuilt=True,
               solid_count=record["bodies"], volume_m3=record["mass"]["volume"],
               area_m2=record["mass"]["area"])
    return row


def calls(record, method):
    return [row.get("result") for row in record["api_calls"] if row["method"] == method]


def read_candidate(folder, phase, job, authorship, source_loc, initial_hash, output_hash):
    record, row = record_for(folder, phase, job)
    checks = record["checks"]
    rebuilds = calls(record, "ForceRebuild3")
    diagnostics = calls(record, "GetWhatsWrongCount")
    require(record["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
            and record["job"] == {"phase": row["phase"], "case": authorship}
            and calls(record, "GetPathName")[0] == source_loc
            and record["source_immutable"] is True
            and not record["first_failure"] and not record["cleanup_errors"]
            and len(checks) == row["checks"] and all(item["passed"] is True for item in checks)
            and rebuilds == ([True, True] if row["phase"].endswith("-edit") else [True])
            and bool(diagnostics) and all(code == 0 for code in diagnostics)
            and record["last_body_count"] == {"solid": 1, "sheet": 0}
            and phase["source_sha256"] == initial_hash
            and record["native_sha256"] == phase["artifact_sha256"] == output_hash
            and record["native_bytes"] == phase["artifact_bytes"] > 0,
            "candidate phase lost its distinct native source, clean geometry or artifact")
    row.update(source=initial_hash, result=output_hash, open_status=[0, 0], rebuilt=True)
    return record, row


def observed_state(stage, state):
    body = state["body"]
    mass = body["native"]
    owners = driver_identity(state)
    drivers = state["drivers"]
    require(set(owners) == {SECTION, PATH} and state["configuration"] == "Default"
            and mass["accuracy_level"] == 2 and mass["selected_solid"] is True
            and mass["use_system_units"] is True and mass["manual_overrides"] is False,
            "native sweep lost its two editable profiles or valid high accuracy mass")
    return {"stage": stage, "drivers": [[*owners[name][0], *owners[name][1:]] for name in (SECTION, PATH)],
            "section_diameter_m": drivers[SECTION]["value_m"], "path_radius_m": drivers[PATH]["value_m"],
            "solid_count": 1, "faces": body["topology"]["faces"], "tree_rows": len(state["tree"]),
            "volume_m3": mass["volume"], "area_m2": mass["area"], "mass_kg": mass["mass"], "com_m": mass["com"]}


def read_lifecycles(records, expected, derivatives):
    baseline = records["candidate-open"]["reopened"]
    require(records["candidate-open"]["cold_solid_count"] == 1
            and records["candidate-open"]["cold_diagnostics"] == 0
            and records["candidate-open"]["cold_ordered_tree"] == baseline["tree"]
            and topology_signature(records["candidate-open"]["before_explicit_rebuild"])
            == topology_signature(baseline["body"]), "original cold tree or body differs")
    states = [observed_state("initial", baseline)]
    statuses, setters = [], []
    count = compare_source(baseline, expected["original"])
    for role, driver, other in (("section", SECTION, PATH), ("path", PATH, SECTION)):
        edited, reopen = records[f"{role}-edit"], records[f"{role}-reopen"]
        start, finish, saved = edited["reopened"], edited["edited"], reopen["reopened"]
        require(all(stable_owners(state, baseline) for state in (start, finish, saved))
                and all(state["drivers"][other]["value_m"] == baseline["drivers"][other]["value_m"]
                        for state in (start, finish, saved))
                and all(topology_signature(phase["before_explicit_rebuild"]) == topology_signature(baseline["body"])
                        for phase in (edited, reopen)), "operation changed actual owners, cold topology or other driver")
        require(edited["native_save_status"] == [True, 0, 0]
                and calls(edited, "SetSystemValue3") == [0]
                and edited["edit"] == {"source": start["drivers"][driver], "role": role, "success": True,
                                       "requested_m": finish["drivers"][driver]["value_m"]}
                and finish["drivers"][driver]["value_m"] != start["drivers"][driver]["value_m"]
                and str(derivatives[role]) in calls(edited, "GetPathName")[1:]
                and edited["native_bytes"] == reopen["native_bytes"],
                "actual edited driver did not save at its separate matching locator")
        states.extend((observed_state(f"{role}-edited", finish), observed_state(f"{role}-reopen", saved)))
        statuses.append(edited["native_save_status"])
        setters.append(calls(edited, "SetSystemValue3")[0])
        for state, source_role in zip((start, finish, saved), ("original", role, role), strict=True):
            count += compare_source(state, expected[source_role])
    return states, statuses, setters, count


def read_slot(packet, capture, terminal, case, comparison, portable, job):
    slot = terminal["slot"]
    hashes = terminal["candidate_sha256"]
    require(terminal["passed"] is True and comparison["slot"] == slot
            and terminal["independent_source_sha256"] == comparison["native_source_sha256"]
            and terminal["independent_observer_sha256"] == comparison["source_receipt_sha256"]
            and len(set(hashes.values())) == 3, "invalid exact independent source pairing")
    folder, original, _ = members(packet, capture, slot, case)
    relative = original.relative_to(packet).as_posix()
    locator = job["candidates"][relative]
    derivatives = {role: PureWindowsPath(job["guest_capture"]) / f"Slot{slot + 1:02d}"
                         / (case["name"] + role.title() + "Edit.SLDPRT") for role in ("section", "path")}
    require(digest(original) == hashes["original"] == portable["candidate_sha256"]
            and portable["target"] == locator and portable["runtime_calls"] == 0,
            "complete generated original differs from measured and portable proof")
    records, phases = {}, []
    require(tuple(phase["phase"] for phase in terminal["phases"]) == PHASES, "missing native sweep phases")
    for phase in terminal["phases"]:
        label = phase["phase"]
        role, _, action = label.partition("-")
        opens_save = action == "reopen"
        source_hash = hashes[role] if opens_save else hashes["original"]
        output_hash = hashes[role] if role in derivatives else hashes["original"]
        source_location = str(derivatives[role]) if opens_save else locator
        require(phase["slot"] == slot, "native phase crossed its slot owner")
        records[label], row = read_candidate(folder / label, phase, job, case,
                                             source_location, source_hash, output_hash)
        phases.append(row)
    states, statuses, setters, comparisons = read_lifecycles(records, comparison["states"], derivatives)
    require(comparisons == terminal["paired_numeric_checks"] == 84
            and records["candidate-open"]["native_bytes"] == original.stat().st_size
            and records["candidate-open"]["original_sha256"] == hashes["original"],
            "original or its independent numeric predictions differ")
    row = {"slot": slot, "archive_sha256": hashes["original"], "archive_bytes": original.stat().st_size,
           "locator": locator, "written_at": EPOCH, "section_save_sha256": hashes["section"],
           "path_save_sha256": hashes["path"], "paired_numeric_checks": comparisons,
           "save_status": statuses, "setter_status": setters, "states": states,
           "independent_source_sha256": comparison["native_source_sha256"],
           "independent_observer_sha256": comparison["source_receipt_sha256"]}
    return row, phases


def normalize(root: Path):
    packet = root / "Packet"
    capture = root / "DisclosedRecords"
    job, spec, _ = verify(packet / "SweepJob.json", JOB)
    terminal = checked_json(capture / "Result.json", NATIVE)
    portability = checked_json(PORTABLE_FILE, PORTABLE)
    comparison = checked_json(packet / "DisclosedComparison.json", job["files"]["DisclosedComparison.json"]["sha256"])
    require(job["cohort"] == "disclosed"
            and terminal["schema"] == "kit.sw2026.standard-sweep-cold-result.v1"
            and terminal["passed"] is True and terminal["idle_after"] is True
            and terminal["inputs_unchanged"] is True and terminal["heldout_credit"] == 0
            and terminal["job_sha256"] == JOB and terminal["writer_revision"] == job["writer_revision"]
            and terminal["oracle_build"] == BUILD and terminal["oracle_sha256"] == ORACLE
            and terminal["source_lock_sha256"] == comparison["source_lock_sha256"] == job["source_lock_sha256"]
            and portability["disclosed_native_result_sha256"] == NATIVE
            and portability["disclosed_intents_sha256"] == job["files"]["Spec.json"]["sha256"],
            "receipt does not describe this controlled disclosed cohort")
    originals = [item for item in portability["tested_cases"] if item["state"] == "original"]
    control_hash = job["files"]["Control.SLDPRT"]["sha256"]
    control_path = str(PureWindowsPath(job["guest_packet"]) / "Control.SLDPRT")
    controls = tuple(read_control(capture / f"control-{label}", terminal["controls"][label], job,
                                  control_path, control_hash) for label in ("before", "after"))
    rows, phases, requests = [], [controls[0]], []
    for index, (result, case, expected, proof) in enumerate(
        zip(terminal["cases"], spec["cases"], comparison["cases"], originals, strict=True)
    ):
        require(result["slot"] == index and proof["name"] == case["name"], "crossed disclosure slot")
        row, observed = read_slot(packet, capture, result, case, expected, proof, job)
        rows.append(row)
        phases.extend(observed)
        requests.append({"case": case, "density": spec["density_kg_m3"], "portable": proof})
    phases.append(controls[1])
    require(len(rows) == 2 and len({tuple(row["lifetime"]) for row in phases}) == len(phases)
            == terminal["distinct_processes"] == terminal["started_processes"] == 12,
            "native batch did not retain 12 distinct controlled lifetimes")
    receipt = {"schema": "kit.sw2026.standard-sweep-measurement.v1", "passed": True, "healthy_controls": True,
               "fresh_processes": len(phases), "oracle": {"build": BUILD, "sha256": ORACLE,
                                                          "product": "SOLIDWORKS 2026 SP05.2"},
               "trial_sha256": JOB, "native_result_sha256": NATIVE, "control_sha256": control_hash,
               "cases": rows, "phases": phases}
    return receipt, requests
