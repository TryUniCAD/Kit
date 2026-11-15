from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import platform
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Capture bounded native research observations with an explicit Frida realm")
    parser.add_argument("--frida-dir", type=Path, required=True)
    parser.add_argument("--process", required=True)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--realm", choices=("native", "emulated"), required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--event-budget", type=int, default=100000)
    args = parser.parse_args()
    if not 0 < args.seconds <= 60 or not 1 <= args.event_budget <= 1000000:
        parser.error("duration must be in (0,60] seconds and event budget in1..1000000")
    source = args.script.read_bytes()
    sys.path.insert(0, str(args.frida_dir))
    frida = importlib.import_module("frida")
    record = {
        "authority": "native-api-boundary-observation", "instruction_taint": False,
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "frida_version": frida.__version__, "frida_directory": str(args.frida_dir),
        "process_name": args.process, "pid_requested": args.pid, "realm": args.realm,
        "script_path": str(args.script), "script_sha256": hashlib.sha256(source).hexdigest(),
        "seconds_requested": args.seconds, "event_budget": args.event_budget,
        "started_at": time.time(), "messages": [], "messages_dropped": 0,
        "attached": False, "detached": False,
    }
    session = None
    script = None
    started = time.monotonic()

    def receive(message, data):
        if len(record["messages"]) >= args.event_budget:
            record["messages_dropped"] += 1
            return
        event = {"sequence": len(record["messages"]), "message": message}
        if data is not None:
            event["binary_data_sha256"] = hashlib.sha256(data).hexdigest()
            event["binary_data_bytes"] = len(data)
        record["messages"].append(event)

    try:
        device = frida.get_local_device()
        targets = [p for p in device.enumerate_processes() if p.name.casefold() == args.process.casefold() and (args.pid is None or p.pid == args.pid)]
        if len(targets) != 1:
            raise RuntimeError(f"expected exactly one explicitly named target, found {len(targets)}")
        record["pid"] = targets[0].pid
        session = device.attach(targets[0].pid, realm=args.realm)
        record["attached"] = True
        script = session.create_script(source.decode("utf-8"), name="kit-tupni-observation")
        script.on("message", receive)
        script.load()
        print(json.dumps({"ready": True, "pid": targets[0].pid, "realm": args.realm}), flush=True)
        time.sleep(args.seconds)
    except Exception as error:
        record["exception"] = repr(error)
    finally:
        if script is not None:
            try:
                script.unload()
            except Exception as error:
                record["script_unload_exception"] = repr(error)
        if session is not None:
            try:
                session.detach()
                record["detached"] = True
            except Exception as error:
                record["detach_exception"] = repr(error)
        record["elapsed_seconds"] = time.monotonic() - started
        record["script_errors"] = [event for event in record["messages"] if event["message"].get("type") == "error"]
        args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items() if key not in ("messages", "host")}))
    return int("exception" in record or "detach_exception" in record or "script_unload_exception" in record or bool(record["script_errors"]) or record["messages_dropped"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
