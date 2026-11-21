from argparse import ArgumentParser
import json
from math import isclose
import os
from pathlib import Path
import subprocess
import sys
import time

from FilletModel import require, validate_cases
from FilletPacket import BUILD, CONTROL, ORACLE, digest, inspect_packet, job_bytes

PHASES = ("author", "reopen-edit-save", "edited-reopen")
BRACKETS = ("control-before", "control-after")
TIMEOUT_SECONDS = 180


def write_new(path, value):
    with path.open("xb") as stream:
        stream.write(job_bytes(value))


def verify_runtime_paths(job_path, job):
    require(os.name == "nt", "CAD oracle phases run only on the root-controlled Windows host")
    packet = Path(job["guest_packet"]).resolve()
    capture = Path(job["guest_capture"]).resolve()
    checkout = Path(job["guest_checkout"]).resolve()
    require(job_path.resolve().parent == packet and Path(__file__).resolve().parent == packet / "Tool"
            and packet.drive.casefold() == capture.drive.casefold() == "c:"
            and not capture.is_relative_to(packet) and not packet.is_relative_to(capture)
            and not capture.is_relative_to(checkout) and not packet.is_relative_to(checkout),
            "native phase has an unbound packet, capture or repository path")
    return packet, capture


def phase_worker(job_path, pin, phase_job):
    job = inspect_packet(job_path, pin)
    packet, capture = verify_runtime_paths(job_path, job)
    options = json.loads(phase_job.read_bytes())
    require(options["source_job_sha256"] == pin and phase_job.name == "PhaseJob.json",
            "phase request does not bind the exact source job")
    phase = options["phase"]
    name = options.get("case")
    require(phase in (*PHASES, *BRACKETS), "unexpected native phase role")
    cases = {case["name"]: case for case in validate_cases(json.loads((packet / "Spec.json").read_bytes()))}
    require((phase in BRACKETS and name is None) or (phase in PHASES and name in cases),
            "phase request does not correspond to a disclosed case")
    folder = capture / (phase if name is None else name)
    if name is not None:
        folder = folder / phase
    require(phase_job.resolve().parent == folder.resolve(), "phase output path does not match its source case")
    record = folder / "Record.json"
    require(not record.exists(), "native phase receipt already exists")
    from FilletSourcePhase import run_control, run_source
    if phase in BRACKETS:
        return run_control(packet / "Control.SLDPRT", record)
    import Swapp
    from FilletApi import installed_registration
    constants, _ = installed_registration(Swapp)
    initial = folder.parent / f"{name}.SLDPRT"
    derivative = folder.parent / f"{name}Edited.SLDPRT"
    return run_source(cases[name], phase, (initial, derivative), record, options["input_sha256"], constants)


def launch(job_path, pin, folder, phase, name=None, source=None):
    folder.mkdir(parents=True, exist_ok=False)
    phase_job, record = folder / "PhaseJob.json", folder / "Record.json"
    write_new(phase_job, {"source_job_sha256": pin, "phase": phase, "case": name, "input_sha256": source})
    command = (sys.executable, "-B", str(Path(__file__).resolve()), "--job", str(job_path), "--job-sha256", pin,
               "--phase-job", str(phase_job))
    started = time.monotonic()
    try:
        child = subprocess.run(command, capture_output=True, timeout=TIMEOUT_SECONDS, check=False)
        stdout, stderr, status, timed_out = child.stdout, child.stderr, child.returncode, False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, status, timed_out = error.stdout or b"", error.stderr or b"", None, True
    (folder / "Stdout.txt").write_bytes(stdout)
    (folder / "Stderr.txt").write_bytes(stderr)
    data = json.loads(record.read_bytes()) if record.is_file() else {}
    identity = data.get("oracle_identity", {})
    passed = status == 0 and not timed_out and not stderr and data.get("passed") is True
    if timed_out and identity:
        from AuthorCurves import cleanup_owned_process
        try:
            cleanup = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
        except Exception as error:
            cleanup = {"error": repr(error)}
        write_new(folder / "TimeoutCleanup.json", cleanup)
    summary = {"phase": phase, "passed": passed, "worker_exit_code": status, "worker_timed_out": timed_out,
               "elapsed_seconds": time.monotonic() - started, "phase_job_sha256": digest(phase_job),
               "receipt_sha256": digest(record) if record.is_file() else None,
               "checks": len(data.get("checks", ())), "checks_passed": sum(item["passed"] for item in data.get("checks", ())),
               "open": data.get("open_status"), "native_sha256": data.get("native_sha256"),
               "native_bytes": data.get("native_bytes"), "geometry_siblings": data.get("geometry_siblings", [])}
    return summary, data, (identity["process_id"], identity["process_creation_filetime"]) if identity else None


def check_lifecycle(rows, case, base):
    if len(rows) != len(PHASES) or not all(row["passed"] for row in rows):
        return False
    first, second, third = [json.loads((base / phase / "Record.json").read_bytes()) for phase in PHASES]
    states = (first["authored"], second["reopened"], second["edited"], third["reopened"])
    prefix = states[0]["driver"]["name"].split("@")[:2]
    initial = base / f"{case['name']}.SLDPRT"
    derivative = base / f"{case['name']}Edited.SLDPRT"
    return (
        digest(initial) == first["native_sha256"] and digest(derivative) == second["native_sha256"] == third["native_sha256"]
        and first["native_sha256"] != second["native_sha256"]
        and all(row["tree"] == states[0]["tree"] and row["driver"]["name"].split("@")[:2] == prefix
                and row["definition"]["parents"] == states[0]["definition"]["parents"]
                and row["definition"]["type"] == states[0]["definition"]["type"] for row in states)
        and all(isclose(a, b, rel_tol=0.0, abs_tol=1e-10)
                for a, b in zip(states[0]["body"]["bounds_m"], states[3]["body"]["bounds_m"], strict=True))
        and states[0]["body"]["native"]["volume"] != states[3]["body"]["native"]["volume"]
    )


def run_case(job_path, pin, case, capture, processes):
    rows, source = [], None
    name = case["name"]
    base = capture / name
    for phase in PHASES:
        row, _, identity = launch(job_path, pin, base / phase, phase, name, source)
        rows.append(row)
        if identity:
            processes.append(identity)
        if not row["passed"]:
            break
        source = row["native_sha256"]
    return {"case": name, "phases": rows, "passed": check_lifecycle(rows, case, base),
            "original_sha256": rows[0]["native_sha256"],
            "edited_sha256": rows[1]["native_sha256"] if len(rows) >= 2 else None}


def execute(job_path, pin):
    job = inspect_packet(job_path, pin)
    packet, capture = verify_runtime_paths(job_path, job)
    require(not capture.exists(), "the native capture root already exists")
    cases = validate_cases(json.loads((packet / "Spec.json").read_bytes()))
    import Swapp
    from FilletApi import installed_registration
    require(not Swapp.application_pids(), "an existing SOLIDWORKS session blocks native fillet authoring")
    capture.mkdir(parents=True, exist_ok=False)
    lock = {"schema": "kit.sw2026.edge-fillet-source-lock.v1", "cohort": "disclosed", "oracle_build": BUILD,
            "oracle_sha256": ORACLE, "job_sha256": pin, "source_revision": job["source_revision"],
            "source_tree": job["source_tree"], "spec_sha256": job["files"]["Spec.json"]["sha256"],
            "control_sha256": CONTROL, "registered_api_sha256": None,
            "controls": {}, "sources": [], "writer_output_count": 0, "source_writer_implemented": False,
            "heldout_writer_acceptance": False}
    processes = []
    try:
        before, _, identity = launch(job_path, pin, capture / BRACKETS[0], BRACKETS[0])
        lock["controls"]["before"] = before
        if identity:
            processes.append(identity)
        if before["passed"]:
            _, api = installed_registration(Swapp)
            write_new(capture / "RegisteredApi.json", api)
            lock["registered_api_sha256"] = digest(capture / "RegisteredApi.json")
            for case in cases:
                row = run_case(job_path, pin, case, capture, processes)
                lock["sources"].append(row)
                if not row["passed"]:
                    break
    except Exception as error:
        write_new(capture / "BatchFailure.json", {"error": repr(error)})
        lock["batch_failure"] = True
    finally:
        try:
            after, _, identity = launch(job_path, pin, capture / BRACKETS[1], BRACKETS[1])
            lock["controls"]["after"] = after
            if identity:
                processes.append(identity)
        except Exception as error:
            write_new(capture / "ControlFailure.json", {"error": repr(error)})
            lock["controls"]["after"] = {"passed": False}
    lock["idle_after"] = not Swapp.application_pids() and not Swapp.owned_process_ids()
    try:
        lock["inputs_unchanged"] = inspect_packet(job_path, pin) == job
    except Exception as error:
        write_new(capture / "InputCustodyFailure.json", {"error": repr(error)})
        lock["inputs_unchanged"] = False
    lock["fresh_processes"] = len(processes)
    lock["distinct_processes"] = len(set(processes))
    lock["passed"] = bool(
        not lock.get("batch_failure") and lock["idle_after"] and lock["inputs_unchanged"]
        and lock["fresh_processes"] == lock["distinct_processes"] == 2 + len(PHASES) * len(cases)
        and all(lock["controls"].get(key, {}).get("passed") for key in ("before", "after"))
        and len(lock["sources"]) == len(cases) and all(row["passed"] for row in lock["sources"])
    )
    report = capture / "SourceLock.json"
    write_new(report, lock)
    return {"passed": lock["passed"], "source_lock_sha256": digest(report), "sources": len(lock["sources"]),
            "distinct_processes": lock["distinct_processes"], "writer_output_count": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--job-sha256", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify-packet", action="store_true")
    mode.add_argument("--phase-job", type=Path)
    args = parser.parse_args()
    if args.verify_packet:
        job = inspect_packet(args.job, args.job_sha256)
        validate_cases(json.loads((args.job.parent / "Spec.json").read_bytes()))
        print(json.dumps({"source_job_sha256": args.job_sha256, "bound_files": len(job["files"]),
                          "native_processes_started": 0}))
        return 0
    if args.phase_job:
        return int(not phase_worker(args.job, args.job_sha256, args.phase_job))
    result = execute(args.job, args.job_sha256)
    print(json.dumps(result, allow_nan=False))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
