from argparse import ArgumentParser
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from FilletColdPacket import (
    ARMS, BACKUP, REGISTERED_API, SOURCE, SOURCE_HASH, checked, read_job,
    sha, trial_case, write_new,
)
from FilletModel import require
from FilletPacket import BUILD, ORACLE, digest, job_bytes

ROLES = ("ControlBefore", *ARMS, "ControlAfter")
TIMEOUT = 180


def guest_paths(job_path, job):
    require(os.name == "nt", "the licensed oracle runner is Windows-only")
    packet, run, source = (Path(value) for value in (job["guest_packet"], job["guest_run"], SOURCE))
    require(job_path.resolve().parent == packet and Path(__file__).resolve().parent == packet / "Tool"
            and source.parent.is_dir() and source.parent.resolve() == source.parent
            and run.parent.resolve() == run.parent and not run.is_symlink() and not run.is_junction(),
            "trial uses an unexpected or indirect local guest path")
    return packet, run, source


def arm_pin(job, arm):
    return job["files"][f"{arm}.SLDPRT"]["sha256"]


def restore_original(source, run, job):
    backup = source.with_name(BACKUP)
    if not backup.exists():
        checked(source, SOURCE_HASH)
        require(not backup.is_symlink(), "unexpected indirect recovery backup")
        return True
    checked(backup, SOURCE_HASH)
    if source.exists():
        require(not source.is_symlink(), "refusing to move an indirect trial occupant")
        pin = digest(source)
        require(pin in {arm_pin(job, arm) for arm in ARMS},
                "refusing to move a locator occupant outside the exact two diagnostic arms")
        source.rename(run / "RecoveredTrialOccupant.sldprt")
    backup.rename(source)
    checked(source, SOURCE_HASH)
    return not backup.exists()


def check_state(actual, expected):
    require(actual["tree"] == expected["tree"] and actual["driver"]["name"].split("@")[:2] == expected["driver_owners"]
            and actual["definition"]["parents"] == expected["stock_parents"]
            and actual["definition"]["type"] == expected["definition_type"],
            "actual recursive native feature, radius owner or stock dependency changed")


def cold_numeric(cold, expected):
    if not cold or "error" in cold:
        return False
    actual = (cold["volume"], cold["area"], *cold["com"])
    target = (expected["volume"], expected["area"], *expected["com"])
    near_zero = (1e-21, 1e-16, 1e-10, 1e-10, 1e-10)
    return all(math.isfinite(a) and (abs(a - b) <= tolerance if abs(b) < tolerance
                                    else format(a, ".6g") == format(b, ".6g"))
               for a, b, tolerance in zip(actual, target, near_zero, strict=True))


def inspect_arm(packet, source, pin, record, role):
    import Swapp
    from AuthorCurves import Recorder
    from FilletApi import installed_registration
    from FilletAuthor import FilletAuthor
    from FilletSourcePhase import has_exact_identity
    from OracleIdentity import application_identity

    checked(source, pin)
    case = trial_case(packet)
    expected = json.loads((packet / "Expected.json").read_bytes())
    rec = Recorder(record, {"role": role, "input_sha256": pin})
    rec.data["oracle_only"] = True
    session = None
    with Swapp.Dismisser() as monitor:
        try:
            constants, api = installed_registration(Swapp)
            require(sha(job_bytes(api)) == REGISTERED_API, "mismatched native registered type library")
            rec.data["registered_api_sha256"] = REGISTERED_API
            session = rec.call("launch fresh versioned SOLIDWORKS", Swapp.Sw)
            identity = rec.call("measure exact native process identity", application_identity, session.app)
            rec.data["oracle_identity"] = identity
            rec.flush()
            require(has_exact_identity(identity) and session.revision == "34.5.2", "wrong native oracle build")
            author = FilletAuthor(session.app, rec, constants)
            author.model, error, warning = rec.call("open diagnostic part at original locator", session.open, source,
                                                    read_only=True)
            rec.data["open_status"] = {"opened": author.model is not None, "errors": error, "warnings": warning}
            rec.flush()
            require(author.model is not None, "native OpenDoc6 returned no fillet document")
            require(Path(str(author.get(author.model, "GetPathName"))).resolve() == source,
                    "native open did not use the exact trial locator")
            bodies = rec.call("measure cold solid count", Swapp.bodies, author.model)
            diagnostics = int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))
            mass = rec.call("measure cold mass before explicit rebuild", Swapp.mass, author.model) if bodies == 1 else None
            rec.data["cold"] = {"bodies": bodies, "diagnostics": diagnostics, "mass": mass}
            rec.flush()

            radius, edit = (case[key] / 1000.0 for key in ("radius_mm", "edit_radius_mm"))
            initial = author.snapshot(case, "rebuilt", radius)
            check_state(initial, expected["reopened"])
            rec.data["cold_measurement_match"] = cold_numeric(mass, initial["body"]["expected"])
            rec.data["rebuild_verified"] = True
            rec.flush()
            author.edit_radius(radius, edit)
            edited = author.snapshot(case, "edited", edit)
            check_state(edited, expected["edited"])
            rec.data["radius_edit_verified"] = True
        except Exception as exc:
            rec.failure(exc)
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception as exc:
                    rec.failure(exc, cleanup=True)
                rec.data["controller_diagnostics"] = session.diagnostics
    rec.data["dialogs"] = monitor.log
    rec.data["input_unchanged"] = source.is_file() and not source.is_symlink() and digest(source) == pin
    rec.data["cold_clean"] = bool(rec.data.get("open_status") == {"opened": True, "errors": 0, "warnings": 0}
                                  and rec.data.get("cold", {}).get("bodies") == 1
                                  and rec.data["cold"]["diagnostics"] == 0
                                  and rec.data.get("cold_measurement_match") is True)
    rec.data["passed"] = bool(rec.data["cold_clean"] and rec.data.get("rebuild_verified")
                              and rec.data.get("radius_edit_verified") and rec.data["input_unchanged"]
                              and not rec.data["first_failure"] and not rec.data["cleanup_errors"]
                              and not rec.data.get("controller_diagnostics") and not rec.data["dialogs"])
    rec.flush()
    return rec.data["passed"]


def phase_worker(packet, run, source, job, role):
    import Swapp

    folder = run / role
    require(folder.is_dir() and folder.resolve() == folder and not Swapp.application_pids(),
            "native worker needs a fresh local folder and an idle oracle")
    record = folder / "Record.json"
    require(not record.exists(), "unexpected pre-existing private native record")
    if role in ARMS:
        checked(source.with_name(BACKUP), SOURCE_HASH)
        return inspect_arm(packet, source, arm_pin(job, role), record, role)
    from FilletSourcePhase import run_control

    checked(source, SOURCE_HASH)
    require(not source.with_name(BACKUP).exists(), "native control started before source custody was restored")
    return run_control(packet / "Control.SLDPRT", record)


def launch(job_path, pin, run, role):
    folder = run / role
    folder.mkdir(exist_ok=False)
    command = (sys.executable, "-B", str(Path(__file__).resolve()), "--job", str(job_path),
               "--job-sha256", pin, "--phase", role)
    try:
        child = subprocess.run(command, capture_output=True, timeout=TIMEOUT, check=False)
        stdout, stderr, status, timed_out = child.stdout, child.stderr, child.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, status, timed_out = exc.stdout or b"", exc.stderr or b"", None, True
    write_new(folder / "Stdout.txt", stdout)
    write_new(folder / "Stderr.txt", stderr)
    record = folder / "Record.json"
    raw = record.read_bytes() if record.is_file() else b""
    data = json.loads(raw) if raw else {}
    identity = data.get("oracle_identity", {})
    from FilletSourcePhase import has_exact_identity

    process = None
    forced_cleanup = False
    if has_exact_identity(identity):
        process = [identity["process_id"], identity["process_creation_filetime"]]
        import Swapp
        if process[0] in Swapp.application_pids():
            from AuthorCurves import cleanup_owned_process

            cleanup = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
            write_new(folder / "OwnedCleanup.json", job_bytes(cleanup))
            forced_cleanup = True
    failure = data.get("first_failure") or {}
    return {"passed": status == 0 and not stderr and data.get("passed") is True, "process": process,
            "verified_execution": process is not None and not timed_out and not stderr and status in (0, 1),
            "worker_exit_code": status, "worker_timed_out": timed_out,
            "raw_receipt_sha256": sha(raw) if raw else None,
            "native_version": identity.get("file_version"), "native_sha256": identity.get("sha256"),
            "registered_api_sha256": data.get("registered_api_sha256"),
            "cold_clean": data.get("cold_clean"), "cold_measurement_match": data.get("cold_measurement_match"),
            "open_status": data.get("open_status"),
            "cold_bodies": data.get("cold", {}).get("bodies"),
            "cold_diagnostics": data.get("cold", {}).get("diagnostics"),
            "rebuild_verified": data.get("rebuild_verified", False),
            "radius_edit_verified": data.get("radius_edit_verified", False),
            "input_unchanged": data.get("input_unchanged"),
            "checks": len(data.get("checks", ())),
            "checks_passed": sum(row["passed"] for row in data.get("checks", ())),
            "failure_type": failure.get("type"), "failure_stage": failure.get("stage"),
            "native_cleanup_problems": bool(forced_cleanup or data.get("cleanup_errors")
                                             or data.get("controller_diagnostics")),
            "dialogs_observed": bool(data.get("dialogs"))}


def run_trial(packet, run, source, job_path, pin, job):
    import Swapp

    backup = source.with_name(BACKUP)
    checked(source, SOURCE_HASH)
    require(not Swapp.application_pids() and not backup.exists() and not backup.is_symlink(),
            "existing SOLIDWORKS process or prior custody backup blocks this trial")
    run.mkdir(exist_ok=False)
    recovery = {"source": str(source), "sha256": SOURCE_HASH, "backup": str(backup),
                "arm_sha256": {arm: arm_pin(job, arm) for arm in ARMS}}
    write_new(run / "Recovery.json", job_bytes(recovery))

    results = {}
    errors = []
    restored = False
    try:
        results["ControlBefore"] = launch(job_path, pin, run, "ControlBefore")
        if results["ControlBefore"]["passed"]:
            require(not Swapp.application_pids(), "native control did not leave the oracle idle")
            checked(source, SOURCE_HASH)
            source.rename(backup)
            checked(backup, SOURCE_HASH)
            for arm in ARMS:
                require(not Swapp.application_pids(), "an unfinished native phase blocks the next arm")
                blob = checked(packet / f"{arm}.SLDPRT", arm_pin(job, arm))
                staging = run / (arm + ".staged")
                write_new(staging, blob)
                staging.rename(source)
                results[arm] = launch(job_path, pin, run, arm)
                require(not Swapp.application_pids(), "the native arm did not leave SOLIDWORKS idle")
                checked(source, arm_pin(job, arm))
                source.rename(run / f"{arm}.Mounted")
    except Exception as exc:
        errors.append(("experiment", repr(exc)))
    finally:
        try:
            require(not Swapp.application_pids(), "oracle is active; recovery is required after it is idle")
            restored = restore_original(source, run, job)
            require(restored, "disclosed source was not restored")
        except Exception as exc:
            errors.append(("source_restoration", repr(exc)))
        if restored:
            try:
                results["ControlAfter"] = launch(job_path, pin, run, "ControlAfter")
            except Exception as exc:
                errors.append(("trailing_control", repr(exc)))

    try:
        input_unchanged = read_job(job_path, pin) == job
    except Exception as exc:
        input_unchanged = False
        errors.append(("final_packet_verification", repr(exc)))
    try:
        checked(source, SOURCE_HASH)
        restored = restored and not backup.exists()
    except Exception as exc:
        restored = False
        errors.append(("final_source_verification", repr(exc)))
    idle = not Swapp.application_pids()
    processes = {tuple(row["process"]) for row in results.values() if row["process"] is not None}
    valid = bool(not errors and restored and idle and input_unchanged and len(processes) == len(ROLES)
                 and set(results) == set(ROLES) and all(row["verified_execution"] for row in results.values())
                 and all(results[role]["passed"] for role in ("ControlBefore", "Intact", "ControlAfter"))
                 and all(not row["native_cleanup_problems"] and not row["dialogs_observed"] for row in results.values())
                 and all(results[role]["input_unchanged"]
                         and results[role]["registered_api_sha256"] == REGISTERED_API for role in ARMS))
    omitted = results.get("OmitPartition", {})
    if not valid:
        outcome = "inconclusive"
    elif omitted["passed"]:
        outcome = "clean_cold_rebuild_and_edit_with_partition_omitted"
    elif omitted["rebuild_verified"] and omitted["radius_edit_verified"]:
        outcome = "rebuild_and_edit_only_with_partition_omitted"
    else:
        outcome = "did_not_rebuild_and_edit_with_partition_omitted"

    if errors:
        write_new(run / "RawErrors.json", job_bytes(errors))
    receipt = {"schema": "kit.sw2026.edge-fillet-cold-diagnostic-result.v1", "job_sha256": pin,
               "source_sha256": SOURCE_HASH, "mutation": job["mutation"], "outcome": outcome,
               "comparison_valid": valid, "phases": results, "distinct_processes": len(processes),
               "source_restored": restored, "oracle_idle": idle, "packet_unchanged": input_unchanged,
               "supervisor_error_stages": [stage for stage, _ in errors],
               "writer_output_count": 0, "native_writer_or_heldout_credit": 0}
    receipt_path = run / "Result.json"
    write_new(receipt_path, job_bytes(receipt))
    return {"comparison_valid": valid, "outcome": outcome, "source_restored": restored,
            "result_sha256": digest(receipt_path)}


def main():
    parser = ArgumentParser(description="run or recover the exact disclosed fillet partition oracle experiment")
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--job-sha256", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--phase", choices=ROLES)
    mode.add_argument("--verify-packet", action="store_true")
    mode.add_argument("--recover", action="store_true")
    args = parser.parse_args()
    job = read_job(args.job, args.job_sha256)
    if args.verify_packet:
        trial_case(args.job.parent)
        print(json.dumps({"job_sha256": args.job_sha256, "bound_files": len(job["files"]), "native_launches": 0}))
        return 0
    packet, run, source = guest_paths(args.job, job)
    if args.phase:
        return int(not phase_worker(packet, run, source, job, args.phase))
    if args.recover:
        import Swapp

        require(run.is_dir() and run.resolve() == run and (run / "Recovery.json").is_file()
                and not Swapp.application_pids(), "recovery requires the pinned interrupted job and an idle oracle")
        restored = restore_original(source, run, job)
        print(json.dumps({"source_restored": restored, "native_launches": 0}))
        return int(not restored)
    result = run_trial(packet, run, source, args.job, args.job_sha256, job)
    print(json.dumps(result, sort_keys=True))
    return int(not result["comparison_valid"])


if __name__ == "__main__":
    raise SystemExit(main())
