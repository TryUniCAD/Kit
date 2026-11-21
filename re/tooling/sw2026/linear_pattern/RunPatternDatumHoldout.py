from argparse import ArgumentParser
from math import dist, isclose
from pathlib import Path
from subprocess import DEVNULL, STDOUT, run
import json
import os
import sys
import time

from PatternDatumHoldoutIntent import ROLE_ORDER, SCHEMA as PRIVATE_SCHEMA, SLOTS
from PatternDatumHoldoutIntent import case_from_seed, intent_spec, new_intent, require_private_dir
from PatternDatumHoldoutPacket import BUILD, CONTROLS, ORACLE, PHASES, PRIVATE_ROOT, TRIAL, verify
from PatternEnvelopePacket import checked, digest, encode, require


INTENT_SCHEMA = "kit.sw2026.linear-pattern-datum-holdout-intent-lock.v1"
LOCK_SCHEMA = "kit.sw2026.linear-pattern-datum-holdout-source-lock.v1"


def publish(path, value):
    with path.open("xb") as stream:
        stream.write(encode(value))
        stream.flush()
        os.fsync(stream.fileno())
    return digest(path.read_bytes())


def locations(pin):
    require(os.name == "nt", "guest-only custody")
    packet = Path(__file__).resolve().parents[1]
    manifest = verify(packet, pin)
    shared = Path(manifest["guest_root"])
    private = Path(PRIVATE_ROOT)
    require((shared / "Packet").resolve() == packet and shared.name == TRIAL,
            "wrong public intake locator")
    require_private_dir(private, private)
    return packet, shared / "Public", private, manifest


def seal(pin):
    _, public, private, manifest = locations(pin)
    require(not public.exists() and not private.exists(), "use a fresh separate private intake")
    private.mkdir(exist_ok=False)
    require_private_dir(private, private)
    frozen = new_intent(pin, manifest["source_revision"], time.time_ns())
    private_pin = publish(private / "FrozenIntent.json", frozen)
    public.mkdir(exist_ok=False)
    lock = {
        "schema": INTENT_SCHEMA, "packet_sha256": pin, "cohort": "heldout",
        "source_revision": manifest["source_revision"], "writer_source_tree": manifest["writer_source_tree"],
        "sealed_at_unix_ns": frozen["sealed_at_unix_ns"], "private_intent_sha256": private_pin,
        "slots": [{"slot": row["slot"], "intent_sha256": digest(encode(row))} for row in frozen["cases"]],
        "private_data_guest_only": True, "writer_output_count": 0, "native_processes_started": 0,
    }
    return publish(public / "IntentLock.json", lock)


def private_intent(public, private, manifest, pin, seal_pin):
    receipt = json.loads(checked(public / "IntentLock.json", seal_pin))
    frozen_bytes = checked(private / "FrozenIntent.json", receipt["private_intent_sha256"])
    frozen = json.loads(frozen_bytes)
    require(receipt["schema"] == INTENT_SCHEMA and frozen["schema"] == PRIVATE_SCHEMA
            and receipt["cohort"] == frozen["cohort"] == manifest["cohort"] == "heldout"
            and receipt["packet_sha256"] == frozen["packet_sha256"] == pin
            and receipt["source_revision"] == frozen["source_revision"] == manifest["source_revision"]
            and receipt["writer_source_tree"] == manifest["writer_source_tree"]
            and receipt["sealed_at_unix_ns"] == frozen["sealed_at_unix_ns"]
            and receipt["writer_output_count"] == receipt["native_processes_started"] == 0
            and receipt["private_data_guest_only"] is True
            and [row["slot"] for row in receipt["slots"]] == list(SLOTS)
            and receipt["slots"] == [{"slot": row["slot"], "intent_sha256": digest(encode(row))}
                                     for row in frozen["cases"]]
            and encode(frozen["cases"]) == encode(case_from_seed(frozen["guest_seed"])),
            "sealed private intent no longer matches its public hash and independent authoring rules")
    return receipt, frozen


def observe_controls(packet, work, side):
    import Swapp
    from AuthorLinearPatternSources import control_phase

    receipts, process_ids, observations = [], [], []
    for index, (name, (_, pin)) in enumerate(CONTROLS.items(), start=1):
        if Swapp.application_pids():
            receipts.append({"control_slot": index, "role": side, "input_sha256": pin, "passed": False})
            break
        output = work / f"Control{side.title()}{index}.json"
        receipt, identity = control_phase(packet / "Controls" / name, pin, output)
        data = json.loads(checked(output, receipt["record_sha256"]))
        process = data.get("oracle_identity", {})
        healthy = bool(receipt["passed"] and process.get("file_version") == BUILD and process.get("sha256") == ORACLE
                       and identity is not None and identity == process.get("process_creation_filetime")
                       and not Swapp.application_pids())
        receipts.append({"control_slot": index, "role": side, "input_sha256": pin,
                         "record_sha256": receipt["record_sha256"], "passed": healthy})
        if identity is not None:
            process_ids.append(identity)
        observations.append(data)
    return receipts, process_ids, observations


def preserve_controls(before, after):
    for original, repeated in zip(before, after, strict=True):
        require(original["bodies"] == repeated["bodies"] and original["features"] == repeated["features"]
                and all(isclose(original["mass"][key], repeated["mass"][key], rel_tol=5e-7)
                        for key in ("volume", "area"))
                and dist(original["mass"]["com"], repeated["mass"]["com"]) <= 1e-10,
                "actual pristine control geometry or tree differs across its bracket")


def source_inputs(snapshot):
    pattern = snapshot["pattern"]
    return {
        "tree": snapshot["tree"], "plate": snapshot["plate_profile"], "seed": snapshot["seed_profile"],
        "plate_boss": snapshot["plate_boss"], "seed_boss": snapshot["seed_boss"],
        "datum": snapshot["datum"], "pattern_parents": pattern["parents"], "seeds": pattern["seeds"],
        "driver_names": {key: name.split("@")[:2] for key, name in pattern["dimensions"]["bindings"].items()},
        "independent_parameters": {key: value for key, value in pattern["values"].items()
                                   if key not in ("D1Spacing", "D1TotalInstances")},
    }


def validate_source_phases(record, source):
    actual = {
        "original": (record["author"]["authored"], record["pristine-reopen"]["reopened"]),
        "spacing": (record["spacing-edit"]["edited"], record["spacing-reopen"]["reopened"]),
        "instances": (record["instances-edit"]["edited"], record["instances-reopen"]["reopened"]),
    }
    baseline = source_inputs(actual["original"][1])
    all_states = [state for stages in actual.values() for state in stages]
    all_states.extend(record[role + "-edit"]["pre_edit"] for role in ROLE_ORDER[1:])
    require(all(source_inputs(state) == baseline for state in all_states),
            "unrelated source owner, profiles, real direction or unchanged driver differ")
    for role, snapshots in actual.items():
        expected = source["design"]["states"][role]
        for state in snapshots:
            values = state["pattern"]["values"]
            require(isclose(values["D1Spacing"], expected["spacing_m"], rel_tol=5e-7)
                    and values["D1TotalInstances"] == expected["count"]
                    and encode(state["expected"]) == encode(expected["expected_final"]),
                    "saved source and frozen independent predictions disagree")
        if role != "original":
            edit = record[role + "-edit"]["edit"]
            require(edit["role"] == role and edit["setter_status"] == 0 and edit["pristine_branch"]
                    and edit["actual_dimension_full_name"].split("@")[:2] == baseline["driver_names"][role],
                    "native edit did not change its exact owned driving dimension")
    require(all(data["checks"] and all(check["passed"] for check in data["checks"]) for data in record.values()),
            "one source phase lacks clean numerical measurements")


def observe_case(home, source, api):
    from AuthorPatternDatumHeight import PatternDatumHeightAuthor
    from AuthorPatternEnvelope import PatternEnvelopeAuthor
    from RunPatternEnvelope import inspect_phase, saved_hash

    class PrivatePatternAuthor(PatternDatumHeightAuthor):
        def __init__(self, application, recorder, bindings, spec):
            super().__init__(application, recorder, bindings, spec)
            self.case["edit_instances"] = spec["arms"][1]["count"]

        def envelope_state(self, label, arm_index):
            value = PatternEnvelopeAuthor.envelope_state(self, label, arm_index)
            self.record_display(label)
            return value

    home.mkdir(exist_ok=False)
    originals = {name: home / basename for name, basename in source["filenames"].items()}
    phases, ids, raw, artifacts = [], [], {}, {}
    for phase in PHASES:
        branch = "instances" if phase.startswith("instances-") else "spacing"
        data, proof = inspect_phase(home, phase, intent_spec(source, branch), api, originals["original"],
                                    originals[branch], artifacts.get("original"), artifacts.get(branch),
                                    author_type=PrivatePatternAuthor, edit_kind=branch, cohort="heldout")
        passed = bool(proof["passed"] and data["source_immutable"] and not data["application_pids_after"])
        phases.append({"phase": phase, "passed": passed, "record_sha256": proof["sha256"]})
        if identity := data.get("oracle_identity"):
            ids.append(identity["process_creation_filetime"])
        if not passed:
            return {"slot": source["slot"], "passed": False, "phases": phases}, ids
        phases[-1]["native_sha256"] = data["artifact"]["sha256"]
        raw[phase] = data
        if phase == "author":
            artifacts["original"] = data["artifact"]
        elif phase.endswith("-edit"):
            artifacts[branch] = data["artifact"]
    try:
        require(set(artifacts) == set(ROLE_ORDER) and len({v["sha256"] for v in artifacts.values()}) == 3
                and all(saved_hash(originals[role]) == row for role, row in artifacts.items()),
                "one immutable native artifact changed after its source phase")
        validate_source_phases(raw, source)
    except Exception as error:
        publish(home / "PrivateComparisonFailure.json", {"error": repr(error)})
        return {"slot": source["slot"], "passed": False, "phases": phases}, ids
    return {"slot": source["slot"], "passed": True, "phases": phases,
            "native_artifacts": {role: artifacts[role]["sha256"] for role in ROLE_ORDER}}, ids


def worker(pin, seal_pin):
    packet, public, private, manifest = locations(pin)
    require_private_dir(private / "Native", private)
    intent, frozen = private_intent(public, private, manifest, pin, seal_pin)
    work = private / "Native"
    work.mkdir(exist_ok=False)
    from RunPatternDatumHeight import registered
    import Swapp

    report = registered(packet)
    metadata_sha = publish(work / "RegisteredApi.json", report)
    result = {"schema": LOCK_SCHEMA, "cohort": "heldout", "packet_sha256": pin, "intent_lock_sha256": seal_pin,
              "source_revision": manifest["source_revision"], "writer_source_tree": manifest["writer_source_tree"],
              "native_build": BUILD, "oracle_sha256": ORACLE, "metadata_sha256": metadata_sha,
              "private_intent_sha256": intent["private_intent_sha256"], "sealed_at_unix_ns": intent["sealed_at_unix_ns"],
              "started_at_unix_ns": time.time_ns(), "private_data_guest_only": True,
              "writer_output_count": 0, "slots": [], "controls": [], "passed": False}
    ids = []
    before = None
    status = "before"
    try:
        require(result["started_at_unix_ns"] > result["sealed_at_unix_ns"], "missing earlier source-intent freeze")
        controls, processes, before = observe_controls(packet, work, "before")
        result["controls"].extend(controls)
        ids.extend(processes)
        require(len(controls) == 2 and all(row["passed"] for row in controls), "before controls refused")
        for source in frozen["cases"]:
            status = source["slot"]
            row, processes = observe_case(work / source["slot"], source, report)
            result["slots"].append(row)
            ids.extend(processes)
            require(row["passed"], "source phase or native comparison refused")
        sealed_artifacts = []
        for drawn, measured in zip(frozen["cases"], result["slots"], strict=True):
            for role, native_pin in measured["native_artifacts"].items():
                checked(work / drawn["slot"] / drawn["filenames"][role], native_pin)
                sealed_artifacts.append(native_pin)
        require(len(sealed_artifacts) == len(set(sealed_artifacts)) == 6, "native source artifacts are not distinct")
        status = "source_complete"
    except Exception as error:
        publish(work / "PrivateFailure.json", {"stage": status, "error": repr(error)})
        result["refused_at"] = status
    finally:
        try:
            controls, processes, after = observe_controls(packet, work, "after")
            result["controls"].extend(controls)
            ids.extend(processes)
            require(len(controls) == 2 and all(row["passed"] for row in controls), "after controls refused")
            if before is not None and all(row["passed"] for row in result["controls"]):
                preserve_controls(before, after)
            require(verify(packet, pin) == manifest and private_intent(public, private, manifest, pin, seal_pin)[0] == intent
                    and not Swapp.application_pids(), "frozen source or process lifetime changed")
            result["complete_distinct_processes"] = len(set(ids))
            result["passed"] = bool(status == "source_complete" and len(result["controls"]) == 4
                                    and [row["slot"] for row in result["slots"]] == list(SLOTS)
                                    and len(ids) == 16 and sorted(set(ids)) == ids)
        except Exception as error:
            publish(work / "PrivateFinalFailure.json", {"error": repr(error)})
            result["refused_at"] = "after_or_final_integrity"
        result["finished_at_unix_ns"] = time.time_ns()
        publish(public / "SourceLock.json", result)
    return int(not result["passed"])


def author(pin, seal_pin):
    _, public, private, _ = locations(pin)
    require(seal_pin is not None and private.is_dir() and not (public / "SourceLock.json").exists(),
            "require a fresh Windows-only sealed intent")
    checked(public / "IntentLock.json", seal_pin)
    require_private_dir(private, private)
    with (private / "NativeTransport.log").open("xb") as log:
        code = ("import runpy,sys; from pathlib import Path; sys.path.insert(0,str(Path(sys.argv[1]).parent)); "
                "entry=runpy.run_path(sys.argv[1]); raise SystemExit(entry['worker'](*sys.argv[2:]))")
        child = run([sys.executable, "-B", "-c", code, str(Path(__file__).resolve()), pin, seal_pin],
                    cwd=str(private), stdin=DEVNULL, stdout=log, stderr=STDOUT, check=False)
    location = public / "SourceLock.json"
    if not location.is_file():
        return {"finished": False, "passed": False, "stage": "private_worker"}
    raw = location.read_bytes()
    receipt = json.loads(raw)
    require(receipt["schema"] == LOCK_SCHEMA and receipt["packet_sha256"] == pin
            and receipt["intent_lock_sha256"] == seal_pin, "private worker published an unrelated receipt")
    return {"finished": True, "passed": receipt["passed"] and child.returncode == 0,
            "source_lock_sha256": digest(raw)}


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("seal", "author"))
    parser.add_argument("--pin", required=True)
    parser.add_argument("--intent-pin")
    args = parser.parse_args()
    try:
        if args.mode == "seal":
            result = {"passed": True, "intent_lock_sha256": seal(args.pin)}
        else:
            result = author(args.pin, args.intent_pin)
    except Exception:
        result = {"passed": False, "stage": args.mode}
    print(json.dumps(result))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
