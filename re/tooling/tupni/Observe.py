from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import platform
import runpy
import struct
import sys
import time
from pathlib import Path


def image_identity(path):
    data = path.read_bytes()
    result = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "pe_machine": None}
    if data[:2] == b"MZ" and len(data) >= 64:
        offset = struct.unpack_from("<I", data, 60)[0]
        if offset + 6 <= len(data) and data[offset:offset + 4] == b"PE\0\0":
            result["pe_machine"] = hex(struct.unpack_from("<H", data, offset + 4)[0])
    return result


def main():
    parser = argparse.ArgumentParser(description="Capture bounded native research observations with an explicit Frida realm", fromfile_prefix_chars="@")
    parser.add_argument("--frida-dir", type=Path, required=True)
    parser.add_argument("--process", required=True)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--realm", choices=("native", "emulated"), required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--event-budget", type=int, default=100000)
    parser.add_argument("--module-manifest", type=Path)
    parser.add_argument("--profile", choices=("full", "loader", "sketch"), default="full")
    parser.add_argument("--exception-probes", action="store_true")
    parser.add_argument("--prepare-script", type=Path)
    parser.add_argument("--action-script", type=Path)
    parser.add_argument("--action-input", type=Path)
    args = parser.parse_args()
    if not 0 < args.seconds <= 60 or not 1 <= args.event_budget <= 1000000:
        parser.error("duration must be in (0,60] seconds and event budget in1..1000000")
    source = args.script.read_bytes()
    sys.path.insert(0, str(args.frida_dir))
    record = {
        "authority": "native-api-boundary-observation", "instruction_taint": False,
        "host": {"platform": platform.platform(), "machine": platform.machine(), "working_directory": str(Path.cwd())},
        "argument_files": [image_identity(Path(value[1:])) for value in sys.argv[1:] if value.startswith("@")],
        "frida_directory": str(args.frida_dir),
        "process_name": args.process, "pid_requested": args.pid, "realm": args.realm,
        "script_path": str(args.script), "script_sha256": hashlib.sha256(source).hexdigest(),
        "seconds_requested": args.seconds, "event_budget": args.event_budget,
        "profile": args.profile,
        "exception_probes": args.exception_probes,
        "started_at": time.time(), "messages": [], "messages_dropped": 0,
        "attached": False, "detached": False,
    }
    session = None
    script = None
    preparation = None
    prepared = None
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

    def detached(reason, crash):
        record["detach_event"] = {"reason": str(reason), "crash": None if crash is None else str(crash)}
        record["detached"] = True

    try:
        record["python_image"] = image_identity(Path(sys.executable))
        record["frida_image"] = image_identity(args.frida_dir / "frida" / "_frida.pyd")
        frida = importlib.import_module("frida")
        record["frida_version"] = frida.__version__
        if args.prepare_script is not None:
            record["prepare_path"] = str(args.prepare_script)
            record["prepare_sha256"] = hashlib.sha256(args.prepare_script.read_bytes()).hexdigest()
            manager = runpy.run_path(str(args.prepare_script))["prepare"]()
            prepared = manager.__enter__()
            preparation = manager
            record["preparation_result"] = prepared["identity"]
        device = frida.get_local_device()
        targets = [p for p in device.enumerate_processes() if p.name.casefold() == args.process.casefold() and (args.pid is None or p.pid == args.pid)]
        if len(targets) != 1:
            raise RuntimeError(f"expected exactly one explicitly named target, found {len(targets)}")
        record["pid"] = targets[0].pid
        session = device.attach(targets[0].pid, realm=args.realm)
        session.on("detached", detached)
        record["attached"] = True
        script = session.create_script(source.decode("utf-8"), name="kit-tupni-observation")
        script.on("message", receive)
        script.load()
        if args.module_manifest is not None:
            expected = json.loads(args.module_manifest.read_text(encoding="utf-8"))
            modules = script.exports_sync.moduleidentity()
            record["module_runtime"] = modules
            record["module_images"] = {}
            for module in modules:
                record["module_images"][module["name"]] = image_identity(Path(module["path"]))
            for name, digest in expected.items():
                matches = [module for module in modules if module["name"].casefold() == name.casefold()]
                if len(matches) != 1:
                    raise RuntimeError(f"expected one loaded module {name}, found {len(matches)}")
                identity = image_identity(Path(matches[0]["path"]))
                record["module_images"][name] = identity
                if identity["sha256"] != digest:
                    raise RuntimeError(f"loaded module image differs from the selected analysis target: {name}")
            record["hook_activation"] = script.exports_sync.activate(args.profile, args.exception_probes)
            if prepared is not None:
                prepared["trace"] = script.exports_sync
        print(json.dumps({"ready": True, "pid": targets[0].pid, "realm": args.realm}), flush=True)
        if args.action_script is not None:
            record["action_path"] = str(args.action_script)
            record["action_sha256"] = hashlib.sha256(args.action_script.read_bytes()).hexdigest()
            if args.action_input is not None:
                record["action_input"] = image_identity(args.action_input)
            action = runpy.run_path(str(args.action_script))
            record["action_result"] = action["exercise"](args.action_input, prepared)
        time.sleep(args.seconds)
        if args.module_manifest is not None:
            record["producer_statistics"] = script.exports_sync.statistics()
            if record["producer_statistics"]["dropped"]:
                raise RuntimeError("native producer event budget was exhausted")
    except Exception as error:
        record["exception"] = repr(error)
    finally:
        if script is not None and "hook_activation" in record:
            try:
                record["producer_statistics"] = script.exports_sync.statistics()
            except Exception as error:
                record["statistics_exception"] = repr(error)
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
        if preparation is not None:
            try:
                preparation.__exit__(None, None, None)
            except Exception as error:
                record["preparation_cleanup_exception"] = repr(error)
        record["elapsed_seconds"] = time.monotonic() - started
        record["script_errors"] = [event for event in record["messages"] if event["message"].get("type") == "error"]
        args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items() if key not in ("messages", "host")}))
    return int("exception" in record or "detach_exception" in record or "script_unload_exception" in record or "preparation_cleanup_exception" in record or "statistics_exception" in record or bool(record["script_errors"]) or record["messages_dropped"] != 0 or record.get("producer_statistics", {}).get("dropped", 0) != 0)


if __name__ == "__main__":
    raise SystemExit(main())
