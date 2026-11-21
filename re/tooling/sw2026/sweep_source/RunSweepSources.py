import argparse
import json
import subprocess
import sys
from pathlib import Path

from SweepModel import DRIVERS, PATH, PHASES, SECTION, require
from SweepPacket import BUILD, CONTROL, ORACLE, digest, local_roots, stage_guest, valid_hash, verify, write_new

LOCK_SCHEMA = "kit.sw2026.standard-sweep-source-lock.v1"
CONTROLS = ("control-before", "control-after")
PROCESS_COUNT = len(PHASES) * 2 + len(CONTROLS)


def case_paths(capture, slot, case):
    folder = capture / f"Slot{slot + 1:02d}"
    original = folder / (case["name"] + ".SLDPRT")
    derivatives = {role: folder / (case["name"] + role.title() + "Edit.SLDPRT") for role in DRIVERS}
    return folder, original, derivatives


def phase_worker(job_path, pin, phase, slot, source_hash):
    job, spec, plans = verify(job_path, pin, permit_private=True)
    packet, capture = local_roots(job_path, job)
    if phase in CONTROLS:
        require(slot is source_hash is None, "control phase cannot carry a source")
        folder = capture / phase
    else:
        require(phase in PHASES and slot is not None and 0 <= slot < len(spec["cases"]), "invalid sweep phase or slot")
        require(source_hash is None if phase == "author" else valid_hash(source_hash), "phase source pin differs")
        case = spec["cases"][slot]
        base, original, derivatives = case_paths(capture, slot, case)
        folder = base / phase
    record = folder / "Record.json"
    authorization = {"phase": phase, "slot": slot, "source_sha256": source_hash, "job_sha256": pin}
    require(folder.is_dir() and folder.resolve() == folder and not record.exists()
            and json.loads((folder / "Phase.json").read_bytes()) == authorization, "phase destination is not owned by this job")
    if phase in CONTROLS:
        from FilletSourcePhase import run_control

        return run_control(packet / "Control.SLDPRT", record)
    import Swapp
    from SweepApi import inspect_registration
    from SweepPhase import run_native

    constants, api = inspect_registration(Swapp)
    require(api == json.loads((capture / "RegisteredApi.json").read_bytes()), "registered API changed after preflight")
    return run_native(case, plans[case["name"]], spec["density_kg_m3"], phase, original, derivatives,
                      source_hash, record, constants)


def launch(job, pin, folder, phase, processes, slot=None, source=None):
    folder.mkdir(parents=True, exist_ok=False)
    entry = {"phase": phase, "slot": slot, "source_sha256": source, "job_sha256": pin}
    write_new(folder / "Phase.json", entry)
    command = [sys.executable, "-E", "-B", str(Path(__file__).resolve()), "--job", str(job), "--pin", pin, "--phase", phase]
    if slot is not None:
        command.extend(("--slot", str(slot)))
    if source is not None:
        command.extend(("--source", source))
    try:
        result = subprocess.run(command, capture_output=True, timeout=180, check=False)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = None, error.stdout or b"", error.stderr or b""
    with (folder / "Stdout.txt").open("xb") as stream:
        stream.write(stdout)
    with (folder / "Stderr.txt").open("xb") as stream:
        stream.write(stderr)
    record = folder / "Record.json"
    data = json.loads(record.read_bytes()) if record.is_file() else {}
    identity = data.get("oracle_identity")
    if identity:
        processes.append((identity["process_id"], identity["process_creation_filetime"]))
    if code is None and identity:
        from AuthorCurves import cleanup_owned_process

        try:
            recovery = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
        except Exception as error:
            recovery = {"error": repr(error)}
        write_new(folder / "TimeoutCleanup.json", recovery)
    row = entry | {"passed": code == 0 and not stderr and data.get("passed") is True,
                   "worker_exit_code": code, "timed_out": code is None,
                   "receipt_sha256": digest(record) if record.is_file() else None,
                   "artifact_sha256": data.get("native_sha256"), "artifact_bytes": data.get("native_bytes"),
                   "checks": len(data.get("checks", ())),
                   "checks_passed": sum(item["passed"] for item in data.get("checks", ()))}
    return row, data


def driver_identity(state):
    return {name: (tuple(row["name"].split("@")[:2]), row["display_kind"], row["driven"], row["read_only"])
            for name, row in state["drivers"].items()}


def topology_signature(body):
    topology = body["topology"]
    return tuple(topology[key] for key in ("faces", "edges", "vertices")), sorted(
        (row["type"], row["torus"], row["producer"], row["producer_type"]) for row in topology["face_rows"])


def stable_owners(state, first):
    return (state["tree"] == first["tree"] and state["configuration"] == first["configuration"]
            and state["definition"] == first["definition"]
            and driver_identity(state) == driver_identity(first)
            and topology_signature(state["body"]) == topology_signature(first["body"]))


def verify_lifecycle(original, derivatives, records):
    first = records["author"]
    baseline = first["authored"]
    require(digest(original) == first["native_sha256"], "authored sweep changed after first close")
    files = {"original": first["native_sha256"]}
    for role, untouched in (("section", PATH), ("path", SECTION)):
        edit, reopen = (records[f"{role}-{action}"] for action in ("edit", "reopen"))
        files[role] = edit["native_sha256"]
        require(digest(derivatives[role]) == files[role] == reopen["native_sha256"],
                f"{role} edit output changed after save")
        states = edit["reopened"], edit["edited"], reopen["reopened"]
        require(all(stable_owners(state, baseline) for state in states),
                f"{role} edit lifecycle changed actual feature tree, configuration, selection, driving owner or topology")
        require(all(state["drivers"][untouched]["value_m"] == baseline["drivers"][untouched]["value_m"]
                    for state in states), f"{role} edit changed the other independent driving value")
        require(all(topology_signature(phase["before_explicit_rebuild"]) == topology_signature(baseline["body"])
                    for phase in (edit, reopen)), f"{role} fresh open changed actual cold topology")
        require(states[0]["body"]["native"]["volume"] != states[2]["body"]["native"]["volume"],
                f"{role} driving edit did not persist distinct native geometry")
    require(len(set(files.values())) == len(files), "source and derivative hashes must all differ")
    return {"artifact_sha256": files, "snapshots": 7, "cold_snapshots": 4, "tree_rows": len(baseline["tree"])}


def run_case(job_path, pin, capture, slot, case, processes):
    folder, original, derivatives = case_paths(capture, slot, case)
    phases, receipts, pins = [], {}, {}
    for phase in PHASES:
        role, _, action = phase.partition("-")
        source = pins[role] if action == "reopen" else pins.get("original")
        row, receipt = launch(job_path, pin, folder / phase, phase, processes, slot, source)
        phases.append(row)
        receipts[phase] = receipt
        if not row["passed"]:
            return {"slot": slot, "phases": phases, "passed": False}
        if action != "reopen":
            pins["original" if phase == "author" else role] = row["artifact_sha256"]
    try:
        lifecycle = verify_lifecycle(original, derivatives, receipts)
    except ValueError as error:
        write_new(folder / "LifecycleFailure.json", {"error": str(error)})
        return {"slot": slot, "phases": phases, "passed": False, "lifecycle_failed": True}
    return {"slot": slot, "phases": phases, "passed": True} | lifecycle


def execute(job_path, pin):
    job, spec, _ = verify(job_path, pin, permit_private=True)
    _, capture = local_roots(job_path, job)
    import Swapp
    from SweepApi import inspect_registration

    require(not capture.exists() and not Swapp.application_pids() and not Swapp.owned_process_ids(),
            "capture already exists or native application is active")
    capture.mkdir(parents=True, exist_ok=False)
    lock = {"schema": LOCK_SCHEMA, "cohort": job["cohort"], "job_sha256": pin, "source_revision": job["source_revision"],
            "source_tree": job["source_tree"], "oracle_build": BUILD, "oracle_sha256": ORACLE, "control_sha256": CONTROL,
            "spec_sha256": job["files"]["Spec.json"]["sha256"], "prediction_sha256": job["files"]["Predictions.json"]["sha256"],
            "controls": {}, "sources": [], "api_sha256": None, "writer_output_count": 0, "heldout_writer_acceptance": False}
    processes = []
    try:
        before, _ = launch(job_path, pin, capture / CONTROLS[0], CONTROLS[0], processes)
        lock["controls"]["before"] = before
        if before["passed"]:
            _, api = inspect_registration(Swapp)
            api_path = capture / "RegisteredApi.json"
            write_new(api_path, api)
            lock["api_sha256"] = digest(api_path)
            for slot, case in enumerate(spec["cases"]):
                result = run_case(job_path, pin, capture, slot, case, processes)
                lock["sources"].append(result)
                if not result["passed"]:
                    break
    except Exception as error:
        write_new(capture / "BatchFailure.json", {"error": repr(error)})
        lock["batch_failure"] = True
    finally:
        try:
            after, _ = launch(job_path, pin, capture / CONTROLS[1], CONTROLS[1], processes)
            lock["controls"]["after"] = after
        except Exception as error:
            write_new(capture / "ControlFailure.json", {"error": repr(error)})
            lock["controls"]["after"] = {"passed": False}
    lock["idle_after"] = not Swapp.application_pids() and not Swapp.owned_process_ids()
    try:
        lock["inputs_unchanged"] = verify(job_path, pin, permit_private=True)[0] == job
    except Exception as error:
        write_new(capture / "InputCustodyFailure.json", {"error": repr(error)})
        lock["inputs_unchanged"] = False
    lock["fresh_processes"], lock["distinct_processes"] = len(processes), len(set(processes))
    lock["passed"] = bool(not lock.get("batch_failure") and lock["idle_after"] and lock["inputs_unchanged"]
                          and lock["fresh_processes"] == lock["distinct_processes"] == PROCESS_COUNT
                          and all(lock["controls"].get(key, {}).get("passed") for key in ("before", "after"))
                          and len(lock["sources"]) == 2 and all(row["passed"] for row in lock["sources"]))
    report = capture / "SourceLock.json"
    write_new(report, lock)
    return {"source_lock_sha256": digest(report), "passed": lock["passed"], "distinct_processes": lock["distinct_processes"],
            "sources": len(lock["sources"]), "writer_output_count": 0}


def main():
    parser = argparse.ArgumentParser(description="Capture isolated native Standard-sketch swept bosses")
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify-packet", action="store_true")
    modes.add_argument("--stage-guest", action="store_true")
    modes.add_argument("--phase", choices=(*PHASES, *CONTROLS))
    parser.add_argument("--slot", type=int)
    parser.add_argument("--source")
    args = parser.parse_args()
    if args.verify_packet:
        job, _, _ = verify(args.job, args.pin)
        result = {"job_sha256": args.pin, "bound_files": len(job["files"]), "native_processes": 0}
    elif args.stage_guest:
        result = stage_guest(args.job, args.pin)
    elif args.phase:
        return int(not phase_worker(args.job, args.pin, args.phase, args.slot, args.source))
    else:
        result = execute(args.job, args.pin)
    print(json.dumps(result, allow_nan=False))
    return int(not result.get("passed", True))


if __name__ == "__main__":
    raise SystemExit(main())
