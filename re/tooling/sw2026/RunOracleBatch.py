from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import queue
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def positive_seconds(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("seconds must be finite and positive")
    return result


def nanoseconds(value):
    return max(1, math.ceil(value * 1_000_000_000))


def absolute_host_path(value):
    result = Path(value).expanduser()
    if not result.is_absolute():
        raise argparse.ArgumentTypeError("a host path must be absolute")
    return result


def reject_constant(value):
    raise ValueError(f"nonfinite JSON number: {value}")


def record_state(data):
    if not isinstance(data, dict):
        raise ValueError("a record must contain a JSON object")
    job = data.get("job", {})
    job = job if isinstance(job, dict) else {}
    case = job.get("case", {})
    return {
        "schema": data.get("schema"),
        "stage": data.get("stage"),
        "case": case.get("name") if isinstance(case, dict) else case,
        "phase": job.get("phase"),
        "native_path": job.get("native_path"),
        "source_sha256": job.get("source_sha256"),
        "source_tool_hashes": job.get("tool_hashes"),
        "identity": data.get("identity"),
        "recorded_started_at": data.get("started_at"),
        "recorded_finished_at": data.get("finished_at"),
        "recorded_passed": data.get("passed"),
        "recorded_work_completed": data.get("work_completed"),
        "first_failure": data.get("first_failure"),
        "api_call_count": len(data.get("api_calls") or []),
        "check_count": len(data.get("checks") or []),
    }


def observe_progress(root, interval, events, stop):
    known = {}
    while not stop.is_set():
        changes, errors, present = [], [], []
        try:
            if root.is_symlink():
                raise ValueError("the progress root became a symbolic link")
            for directory, directories, names in os.walk(
                root,
                followlinks=False,
                onerror=lambda error: (
                    errors.append({"error": repr(error)})
                    if not isinstance(error, FileNotFoundError)
                    else None
                ),
            ):
                directories[:] = [
                    name
                    for name in directories
                    if not (Path(directory) / name).is_symlink()
                ]
                if stop.is_set():
                    return
                if "Record.json" not in names:
                    continue
                path = Path(directory) / "Record.json"
                relative = str(path.relative_to(root))
                try:
                    metadata = path.lstat()
                    if not stat.S_ISREG(metadata.st_mode):
                        raise ValueError("a progress record is not a regular file")
                    raw = path.read_bytes()
                    digest = hashlib.sha256(raw).hexdigest()
                    present.append(relative)
                    if known.get(relative) == digest:
                        continue
                    observation = {
                        "path": relative,
                        "sha256": digest,
                        "bytes": len(raw),
                        "mtime_ns": metadata.st_mtime_ns,
                        "observed_monotonic_ns": time.monotonic_ns(),
                        "observed_at": utc_now(),
                    }
                    try:
                        observation["record"] = record_state(
                            json.loads(raw, parse_constant=reject_constant)
                        )
                        observation["json_status"] = "parsed"
                    except (ValueError, TypeError, UnicodeError) as error:
                        observation.update(
                            json_status="unavailable", json_error=repr(error)
                        )
                    known[relative] = digest
                    changes.append(observation)
                except (OSError, ValueError) as error:
                    errors.append({"path": relative, "error": repr(error)})
        except Exception as error:
            errors.append({"error": repr(error)})
        events.put(
            {
                "observed_monotonic_ns": time.monotonic_ns(),
                "observed_at": utc_now(),
                "present_records": present,
                "changes": changes,
                "errors": errors,
            }
        )
        stop.wait(interval)


def write_report(path, report):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=path.name + ".",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(report, stream, indent=2, ensure_ascii=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def drain_progress(events, report, last_progress):
    for _ in range(256):
        try:
            observation = events.get_nowait()
        except queue.Empty:
            return last_progress
        report["progress"]["last_scan"] = {
            key: observation[key]
            for key in ("observed_monotonic_ns", "observed_at", "present_records")
        }
        if observation["errors"]:
            report["progress"]["observation_errors"].append(
                {
                    "observed_at": observation["observed_at"],
                    "errors": observation["errors"],
                }
            )
        for change in observation["changes"]:
            last_progress = max(last_progress, change["observed_monotonic_ns"])
            report["progress"]["records"][change["path"]] = change
            report["progress"]["history"].append(change)
            report["progress"]["last_changed_record"] = change
    return last_progress


def stop_owned_transport(process, terminate_seconds, kill_seconds):
    actions = []
    for method, limit in (("terminate", terminate_seconds), ("kill", kill_seconds)):
        if process.poll() is not None:
            break
        action = {"method": method, "pid": process.pid, "requested_at": utc_now()}
        actions.append(action)
        try:
            getattr(process, method)()
        except OSError as error:
            action["signal_error"] = repr(error)
        try:
            action["returncode"] = process.wait(timeout=limit)
            action["exit_confirmed"] = True
        except subprocess.TimeoutExpired:
            action["exit_confirmed"] = False
        except OSError as error:
            action["wait_error"] = repr(error)
    return {
        "actions": actions,
        "returncode": process.poll(),
        "target": "owned direct host Popen child only",
    }


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Host deadline for one research oracle transport; never CAD acceptance"
    )
    parser.add_argument("--vm", required=True)
    parser.add_argument("--progress-root", required=True, type=absolute_host_path)
    parser.add_argument("--report", type=absolute_host_path)
    parser.add_argument("--prlctl", default="prlctl")
    parser.add_argument("--no-progress-seconds", type=positive_seconds, default=360.0)
    parser.add_argument("--overall-seconds", type=positive_seconds)
    parser.add_argument("--poll-seconds", type=positive_seconds, default=1.0)
    parser.add_argument("--terminate-seconds", type=positive_seconds, default=10.0)
    parser.add_argument("--kill-seconds", type=positive_seconds, default=10.0)
    supplied = sys.argv[1:]
    separator = supplied.index("--") if "--" in supplied else len(supplied)
    args = parser.parse_args(supplied[:separator])
    guest = supplied[separator + 1 :]
    if not guest:
        parser.error("supply the guest executable and arguments after --")
    if not (PureWindowsPath(guest[0]).is_absolute() or Path(guest[0]).is_absolute()):
        parser.error("use an absolute guest executable, preferably Python and a script")
    if sys.platform != "darwin" and not sys.platform.startswith("linux"):
        parser.error("the supervisor supports macOS and Linux hosts only")
    if not args.vm or any("\x00" in value for value in [args.vm, *guest]):
        parser.error(
            "the VM must be nonempty and command arguments must not contain NUL"
        )
    if os.path.lexists(args.progress_root):
        parser.error("the guest progress/output root must be new and must not exist")
    args.progress_root = args.progress_root.resolve()
    report = args.report or args.progress_root.with_name(
        args.progress_root.name + ".Host.json"
    )
    if os.path.lexists(report):
        parser.error("the host report must be new")
    args.report = report.resolve()
    evidence = (
        args.report,
        args.report.with_name(args.report.name + ".stdout.log"),
        args.report.with_name(args.report.name + ".stderr.log"),
    )
    if any(
        path.is_relative_to(args.progress_root)
        or args.progress_root.is_relative_to(path)
        for path in evidence
    ):
        parser.error(
            "host evidence must be separate from the new guest progress/output root"
        )
    executable = shutil.which(args.prlctl)
    if executable is None:
        parser.error("the selected prlctl executable is unavailable")
    args.command = [executable, "exec", args.vm, "--current-user", *guest]
    args.guest = guest
    return args


def run(args):
    started = time.monotonic_ns()
    last_progress = started
    stop = threading.Event()
    events = queue.Queue(maxsize=64)
    process, observer = None, None
    stdout = args.report.with_name(args.report.name + ".stdout.log")
    stderr = args.report.with_name(args.report.name + ".stderr.log")
    for path in (args.report, stdout, stderr):
        if os.path.lexists(path):
            raise FileExistsError(f"refusing to overwrite host evidence: {path}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "kit-sw2026-host-oracle-supervision/1",
        "status": "starting",
        "started_at": utc_now(),
        "started_monotonic_ns": started,
        "host_pid": os.getpid(),
        "host_platform": sys.platform,
        "python_version": sys.version,
        "script": str(Path(__file__).resolve()),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "supervisor_argv": list(sys.argv),
        "command_argv": args.command,
        "guest_argv": args.guest,
        "vm": args.vm,
        "current_user": True,
        "progress_root": str(args.progress_root),
        "report_path": str(args.report),
        "stdout_path": str(stdout),
        "stderr_path": str(stderr),
        "limits_seconds": {
            "no_progress": args.no_progress_seconds,
            "overall": args.overall_seconds,
            "terminate_wait": args.terminate_seconds,
            "kill_wait": args.kill_seconds,
            "poll": args.poll_seconds,
        },
        "progress": {"records": {}, "history": [], "observation_errors": []},
        "guest_state_unknown": True,
        "acceptance": False,
        "acceptance_scope": "research host transport observations only; inspect native batch and controls separately",
        "automatic_guest_kill": False,
        "automatic_vm_reset": False,
        "automatic_retry": False,
        "external_inventory_required_before_another_batch": False,
    }
    exit_code = 125
    with args.report.open("x", encoding="utf-8"):
        pass
    interruption = {}
    previous_handlers = {}

    def record_interruption(number, frame):
        interruption.setdefault("signal", number)

    try:
        for number in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[number] = signal.signal(number, record_interruption)
        with stdout.open("xb") as output, stderr.open("xb") as errors:
            write_report(args.report, report)
            if os.path.lexists(args.progress_root):
                raise RuntimeError(
                    "the progress root appeared before owned transport launch"
                )
            if interruption:
                raise KeyboardInterrupt
            process = subprocess.Popen(
                args.command,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=errors,
                shell=False,
                close_fds=True,
                start_new_session=True,
            )
            report.update(status="running", transport_pid=process.pid)
            observer = threading.Thread(
                target=observe_progress,
                args=(args.progress_root, args.poll_seconds, events, stop),
                daemon=True,
                name="oracle-record-observer",
            )
            observer.start()
            while True:
                last_progress = drain_progress(events, report, last_progress)
                now = time.monotonic_ns()
                returncode = process.poll()
                report.update(
                    last_poll_at=utc_now(),
                    last_poll_monotonic_ns=now,
                    elapsed_ns=now - started,
                    no_progress_elapsed_ns=now - last_progress,
                    transport_returncode=returncode,
                    transport_live=returncode is None,
                    observer_thread_live=observer.is_alive(),
                )
                if returncode is not None:
                    report["status"] = "transport_exited"
                    report["external_inventory_required_before_another_batch"] = (
                        returncode != 0
                    )
                    exit_code = returncode if returncode >= 0 else 128 - returncode
                    break
                if interruption:
                    report.update(status="host_interrupted", interruption=interruption)
                    report["external_inventory_required_before_another_batch"] = True
                    exit_code = 128 + interruption["signal"]
                    break
                no_progress_deadline = last_progress + nanoseconds(
                    args.no_progress_seconds
                )
                overall_deadline = (
                    started + nanoseconds(args.overall_seconds)
                    if args.overall_seconds
                    else None
                )
                due = []
                if now >= no_progress_deadline:
                    due.append("no_progress")
                if overall_deadline is not None and now >= overall_deadline:
                    due.append("overall")
                if due:
                    report.update(status="host_deadline", deadline_kinds=due)
                    report["external_inventory_required_before_another_batch"] = True
                    exit_code = 124
                    break
                write_report(args.report, report)
                remaining = [no_progress_deadline - now]
                if overall_deadline is not None:
                    remaining.append(overall_deadline - now)
                time.sleep(min(args.poll_seconds, min(remaining) / 1_000_000_000))
    except KeyboardInterrupt:
        report.update(
            status="host_interrupted", interruption=interruption or "KeyboardInterrupt"
        )
        report["external_inventory_required_before_another_batch"] = True
        exit_code = 128 + interruption.get("signal", signal.SIGINT)
    except Exception as error:
        report.update(status="host_monitor_failed", error=repr(error))
        report["external_inventory_required_before_another_batch"] = True
        exit_code = 125
    finally:
        stop.set()
        if process is not None and process.poll() is None:
            report["transport_cleanup"] = stop_owned_transport(
                process, args.terminate_seconds, args.kill_seconds
            )
        if observer is not None:
            observer.join(timeout=0.1)
        last_progress = drain_progress(events, report, last_progress)
        returncode = process.poll() if process is not None else None
        if process is not None and returncode is None:
            exit_code = 125
            report["external_inventory_required_before_another_batch"] = True
        report.update(
            finished_at=utc_now(),
            finished_monotonic_ns=time.monotonic_ns(),
            transport_returncode=returncode,
            transport_live=returncode is None if process is not None else None,
            transport_exit_confirmed=(
                returncode is not None if process is not None else None
            ),
            transport_stop_failed=process is not None and returncode is None,
            supervisor_exit_code=exit_code,
        )
        report["elapsed_ns"] = report["finished_monotonic_ns"] - started
        report["no_progress_elapsed_ns"] = (
            report["finished_monotonic_ns"] - last_progress
        )
        try:
            write_report(args.report, report)
        except Exception as error:
            print(
                json.dumps(
                    {"report_write_failed": repr(error), "report": report},
                    allow_nan=False,
                ),
                file=sys.stderr,
                flush=True,
            )
            exit_code = 125
        finally:
            for number, handler in previous_handlers.items():
                signal.signal(number, handler)
    return exit_code


def main():
    return run(parse_arguments())


if __name__ == "__main__":
    raise SystemExit(main())
