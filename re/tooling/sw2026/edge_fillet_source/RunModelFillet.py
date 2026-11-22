from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
from subprocess import TimeoutExpired, run
import os
import sys

from FilletModel import require
from FilletModelPacket import load_job, locator
from FilletPacket import CONTROL, ORACLE, digest, job_bytes
from FilletStockPacket import ORACLE_AUTHORITY, REGISTERED_API, pinned, sha, write_new

TIMEOUT = 180
CONTROLS = ("ControlBefore", "ControlAfter")
PHASES = ("reopen-edit-save", "edited-reopen")


def phase_dir(root, name, phase):
    run_dir = root / "Run01"
    return run_dir / name / phase if name else run_dir / phase


def run_phase(root, folder, cases, name, phase, input_pin):
    import Swapp
    from FilletApi import installed_registration
    from FilletSourcePhase import run_control, run_source

    where = phase_dir(root, name, phase)
    require(where.is_dir() and where.resolve() == where and not where.is_junction()
            and not Swapp.application_pids(), "model phase requires an idle oracle and exclusive local output")
    record = where / "Record.json"
    require(not record.exists() and not record.is_symlink(), "model fillet phase record already exists")
    if not name:
        require(phase in CONTROLS and input_pin == CONTROL, "unexpected model control phase")
        return run_control(folder / "Control.SLDPRT", record)
    require(name in cases and phase in PHASES, "unexpected model fillet phase")
    constants, api = installed_registration(Swapp)
    require(sha(job_bytes(api)) == REGISTERED_API, "unexpected registered SOLIDWORKS typelib")
    generated = Path(locator(root, name))
    saved = root / "Edited" / f"{name}Edited.SLDPRT"
    inputs = (generated, saved)
    pinned(generated if phase == PHASES[0] else saved, input_pin)
    return run_source(cases[name], phase, inputs, record, input_pin, constants, measure_cold=True)


def summarize(record, exit_code, timed_out, stderr):
    from FilletSourcePhase import has_exact_identity

    raw = record.read_bytes() if record.is_file() else b""
    value = loads(raw) if raw else {}
    identity = value.get("oracle_identity") or {}
    process = [identity.get("process_id"), identity.get("process_creation_filetime")]
    exact = has_exact_identity(identity) and all(type(number) is int and number > 0 for number in process)
    checks = value.get("checks", ())
    states = {label: {"tree": [row["name"] for row in state["tree"]],
                      "volume_area_centroid": [state["body"]["native"][key] for key in ("volume", "area", "com")],
                      "body_counts": state["body"]["counts"], "radius_m": state["driver"]["value_si"],
                      "type": state["definition"]["type"], "parents": state["definition"]["parents"]}
              for label in ("reopened", "edited") if (state := value.get(label))}
    first_failure = value.get("first_failure") or {}
    return {"passed": bool(exact and not timed_out and not stderr and exit_code == 0 and value.get("passed")),
            "process": process if exact else None, "build": identity.get("file_version"),
            "executable_sha256": identity.get("sha256"), "receipt_sha256": sha(raw) if raw else None,
            "worker_status": exit_code, "timed_out": timed_out, "failure_stage": first_failure.get("stage"),
            "failure_type": first_failure.get("type"), "open_status": value.get("open_status"),
            "cold": value.get("before_explicit_rebuild"), "save_status": value.get("native_save_status"),
            "unchanged_input": value.get("source_immutable"), "output_sha256": value.get("native_sha256"),
            "checks": len(checks), "checks_passed": sum(row["passed"] for row in checks), "states": states}


def launch(job_path, pin, root, name, phase, input_pin):
    from AuthorCurves import cleanup_owned_process
    from FilletSourcePhase import has_exact_identity

    where = phase_dir(root, name, phase)
    where.mkdir(parents=True, exist_ok=False)
    command = (sys.executable, "-E", "-B", str(Path(__file__).resolve()), "--job", str(job_path),
               "--job-sha256", pin, "--phase", phase, "--case", name or "control", "--input-sha256", input_pin)
    timed_out = False
    try:
        process = run(command, cwd=Path(__file__).resolve().parent, capture_output=True, timeout=TIMEOUT, check=False)
        stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
    except TimeoutExpired as error:
        stdout, stderr, exit_code, timed_out = error.stdout or b"", error.stderr or b"", None, True
    write_new(where / "Stdout.txt", stdout)
    write_new(where / "Stderr.txt", stderr)
    record = where / "Record.json"
    if timed_out and record.is_file():
        identity = loads(record.read_bytes()).get("oracle_identity") or {}
        if has_exact_identity(identity):
            cleanup = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
            write_new(where / "TimeoutCleanup.json", job_bytes(cleanup))
    return summarize(record, exit_code, timed_out, stderr)


def run_case(job_path, pin, job, root, name):
    source_pin = job["files"][f"Generated/{name}.SLDPRT"]["sha256"]
    rows = {PHASES[0]: launch(job_path, pin, root, name, PHASES[0], source_pin)}
    initial = rows[PHASES[0]]
    if initial["passed"]:
        rows[PHASES[1]] = launch(job_path, pin, root, name, PHASES[1], initial["output_sha256"])
    edited = rows.get(PHASES[1], {})
    agrees = bool(initial["passed"] and edited.get("passed")
                  and initial["states"]["reopened"]["tree"] == initial["states"]["edited"]["tree"]
                  and initial["states"]["edited"]["tree"] == edited["states"]["reopened"]["tree"]
                  and initial["states"]["edited"]["parents"] == edited["states"]["reopened"]["parents"]
                  and initial["states"]["edited"]["type"] == edited["states"]["reopened"]["type"]
                  and initial["output_sha256"] == edited["output_sha256"]
                  and initial["states"]["reopened"]["volume_area_centroid"][0]
                  != edited["states"]["reopened"]["volume_area_centroid"][0])
    return {"passed": agrees, "candidate_sha256": source_pin, "phases": rows}


def execute(job_path, pin, folder, root, job, cases):
    import Swapp

    output_dirs = tuple(root / name for name in ("Candidates", "Edited", "Run01"))
    require(not Swapp.application_pids() and not Swapp.owned_process_ids()
            and not any(item.exists() or item.is_symlink() for item in output_dirs),
            "model fillet bracket needs a fresh workspace and idle SOLIDWORKS")
    for path in output_dirs:
        path.mkdir(exist_ok=False)
    for name in cases:
        basename = f"{name}.SLDPRT"
        raw = pinned(folder / "Generated" / basename, job["files"][f"Generated/{basename}"]["sha256"])
        write_new(Path(locator(root, name)), raw)
    result = {"schema": "kit.sw2026.edge-fillet-model-native.v1", "model_job_sha256": pin,
              "writer_commit": job["writer_commit"], "probe_commit": job["probe_commit"],
              "oracle": ORACLE_AUTHORITY, "controls": {}, "cases": {}, "heldout_sources_read": 0}
    try:
        result["controls"][CONTROLS[0]] = launch(job_path, pin, root, None, CONTROLS[0], CONTROL)
        if result["controls"][CONTROLS[0]]["passed"]:
            for name in cases:
                if Swapp.application_pids():
                    break
                result["cases"][name] = run_case(job_path, pin, job, root, name)
    except Exception as error:
        result["batch_error_type"] = type(error).__name__
        write_new(root / "Run01" / "BatchError.txt", repr(error).encode("utf-8"))
    finally:
        if not Swapp.application_pids():
            try:
                result["controls"][CONTROLS[1]] = launch(job_path, pin, root, None, CONTROLS[1], CONTROL)
            except Exception as error:
                result["later_control_error_type"] = type(error).__name__
                write_new(root / "Run01" / "LaterControlError.txt", repr(error).encode("utf-8"))
    rows = list(result["controls"].values()) + [
        phase for case in result["cases"].values() for phase in case["phases"].values()
    ]
    processes = [tuple(row["process"]) for row in rows if row["process"]]
    result["distinct_native_processes"] = len(set(processes))
    result["unchanged_candidates"] = all(
        digest(Path(locator(root, name))) == job["files"][f"Generated/{name}.SLDPRT"]["sha256"]
        for name in cases
    )
    result["comparison_valid"] = bool(
        all(result["controls"].get(role, {}).get("passed") for role in CONTROLS)
        and not Swapp.application_pids() and not Swapp.owned_process_ids()
        and len(processes) == len(set(processes)) == len(rows) and not result.get("batch_error_type")
        and result["unchanged_candidates"]
    )
    result["passed"] = bool(result["comparison_valid"] and len(rows) == 6
                            and set(result["cases"]) == set(cases)
                            and all(case["passed"] for case in result["cases"].values()))
    raw = job_bytes(result)
    write_new(root / "Run01" / "Result.json", raw)
    print(dumps({"result_sha256": sha(raw), "passed": result["passed"],
                 "comparison_valid": result["comparison_valid"]}, sort_keys=True))
    return result["passed"]


def main():
    parser = ArgumentParser(description="measure two disclosed generated fillets and live edits on the exact Windows oracle")
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--phase")
    parser.add_argument("--case")
    parser.add_argument("--input-sha256")
    args = parser.parse_args()
    folder, guest_root, job, cases = load_job(args.job, args.job_sha256)
    if args.verify:
        require(not args.phase, "transport verification does not open a document")
        print(dumps({"verified_files": len(job["files"]), "native_processes_started": 0}, sort_keys=True))
        return 0
    require(os.name == "nt", "native fillet bracket is Windows-only")
    root = Path(guest_root)
    require(root.is_dir() and root.resolve() == root and not root.is_junction()
            and folder == root / "Packet" and Path(__file__).resolve().parent == folder / "Tool",
            "model fillet bracket must use its exact direct guest locator")
    if args.phase:
        name = None if args.case == "control" else args.case
        return 0 if run_phase(root, folder, cases, name, args.phase, args.input_sha256) else 1
    return 0 if execute(args.job, args.job_sha256, folder, root, job, cases) else 1


if __name__ == "__main__":
    sys.exit(main())
