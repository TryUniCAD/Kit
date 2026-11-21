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


def training_qualification(record):
    reasons = []
    incomplete_count = 0
    action = record.get("action_result", {})
    cases = [item["case"]["name"] for item in action.get("cases", [])]
    counts = {name: {} for name in cases}

    def reason(value):
        if len(reasons) < 256:
            reasons.append(value)

    def inspect(value, path, event):
        nonlocal incomplete_count
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ("complete", "dimension_resolution_complete", "semantic_class_admitted", "layout_read_complete") and child is False:
                    incomplete_count += 1
                    reason({"event": event, "path": path + "." + key, "reason": "incomplete native state"})
                elif key == "error":
                    incomplete_count += 1
                    reason({"event": event, "path": path, "reason": str(child)})
                inspect(child, path + "." + key, event)
            if "points" in value and "arcs" in value and isinstance(value["arcs"].get("raw_count"), int) and value["arcs"]["raw_count"] > 0:
                for key in ("points", "arcs"):
                    scan = value[key]
                    count = scan.get("raw_count")
                    if not scan.get("bounded_scan_complete") or not isinstance(count, int) or scan.get("scanned_count") != count or scan.get("completed_slots") != count or len(scan.get("slots", [])) != count:
                        incomplete_count += 1
                        reason({"event": event, "path": path + "." + key, "reason": "incomplete circle graph scan"})
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, path + f"[{index}]", event)

    if not action.get("passed") or not cases:
        reason({"reason": "training action or case membership is incomplete"})
    for item in record["messages"]:
        message = item["message"]
        payload = message.get("payload")
        if message.get("type") != "send" or not isinstance(payload, dict):
            continue
        phase = payload.get("phase", "")
        matches = [name for name in cases if phase.startswith(name + ":")]
        if not matches:
            continue
        for name in matches:
            kind = payload.get("kind", "")
            counts[name][kind] = counts[name].get(kind, 0) + 1
        inspect(payload, "payload", payload.get("sequence"))
    required = {"radial-engine-leave", "radial-serialize-leave", "radial-raw-word-store", "sketch-whole-update-leave", "sketch-serialize-leave"}
    if action.get("phase") == "author":
        required.add("radial-constructor-leave")
        required.add("circle-api-dispatch")
    for name, observed in counts.items():
        missing = sorted(required - observed.keys())
        if missing:
            reason({"case": name, "reason": "required native boundaries were not observed", "missing": missing})
    stats = record.get("producer_statistics", {})
    if stats.get("training_hook_errors", 0) or stats.get("training_solves", 0) or stats.get("training_events", 0):
        reason({"reason": "native hook errors or unfinished observation scopes", "statistics": stats})
    if not record.get("mapped_training_instructions_verified"):
        reason({"reason": "mapped hook instructions were not verified"})
    if record.get("messages_dropped") or stats.get("dropped") or record.get("script_errors") or not record.get("detached"):
        reason({"reason": "trace drops, script errors or incomplete detach"})
    for key in ("exception", "detach_exception", "script_unload_exception", "preparation_cleanup_exception", "statistics_exception"):
        if key in record:
            reason({"reason": key, "detail": record[key]})
    return {"qualified": not reasons and incomplete_count == 0, "incomplete_native_states": incomplete_count, "reasons": reasons, "reason_limit": 256, "case_event_counts": counts, "field_closure_proven": False, "callback_effects_proven": False, "acceptance": False}


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
    parser.add_argument("--profile", choices=("full", "loader", "sketch", "repair", "frame", "radial-training"), default="full")
    parser.add_argument("--exception-probes", action="store_true")
    parser.add_argument("--prepare-script", type=Path)
    parser.add_argument("--action-script", type=Path)
    parser.add_argument("--action-input", type=Path)
    args = parser.parse_args()
    if not 0 < args.seconds <= 60 or not 1 <= args.event_budget <= 1000000:
        parser.error("duration must be in (0,60] seconds and event budget in1..1000000")
    if args.profile == "radial-training" and (args.module_manifest is None or args.prepare_script is None or args.action_script is None or args.action_input is None):
        parser.error("radial-training requires its pinned module manifest, retained preparation and explicit training action/input")
    if args.profile == "radial-training" and args.output.exists():
        parser.error("radial-training requires an unused observation output path")
    if args.profile == "radial-training" and not args.output.parent.is_dir():
        parser.error("radial-training requires an existing parent for its unused observation output")
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
        if args.profile == "radial-training":
            if prepared is None or record["pid"] != prepared["identity"]["oracle_identity"]["process_id"]:
                raise RuntimeError("radial-training target differs from the retained owned controller")
        session = device.attach(targets[0].pid, realm=args.realm)
        session.on("detached", detached)
        record["attached"] = True
        script = session.create_script(source.decode("utf-8"), name="kit-tupni-observation")
        script.on("message", receive)
        script.load()
        if args.module_manifest is not None:
            expected = json.loads(args.module_manifest.read_text(encoding="utf-8"))
            record["module_manifest"] = image_identity(args.module_manifest)
            if args.profile == "radial-training":
                pinned_path = Path(__file__).with_name("RadialTrainingModules.json")
                if expected != json.loads(pinned_path.read_text(encoding="utf-8")):
                    raise RuntimeError("radial-training module manifest differs from the pinned observation identities")
                record["training_module_manifest"] = image_identity(pinned_path)
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
            if args.profile == "radial-training":
                hook_path = Path(__file__).resolve().parents[2] / "solidworks" / "records" / "RadialTrainingHooks2026.json"
                hook_metadata = json.loads(hook_path.read_text(encoding="utf-8"))
                record["training_hook_metadata"] = image_identity(hook_path)
                expected_windows = hook_metadata["mapped_hook_windows"]
                observed_windows = script.exports_sync.traininghookinstructions()
                record["mapped_training_instructions_verified"] = False
                record["full_mapped_function_bodies_verified"] = False
                record["mapped_training_instruction_windows"] = []
                if len(expected_windows) != 12 or len(observed_windows) != 12:
                    raise RuntimeError("the exact twelve mapped training windows are required")
                for wanted, actual in zip(expected_windows, observed_windows):
                    data = bytes.fromhex(actual["bytes_hex"])
                    digest = hashlib.sha256(data).hexdigest()
                    item = {key: value for key, value in actual.items() if key != "bytes_hex"}
                    item.update(mapped_sha256=digest, expected_sha256=wanted["sha256"], matches=False)
                    record["mapped_training_instruction_windows"].append(item)
                    if any(actual[key] != wanted[key] for key in ("module", "rva", "bytes")) or len(data) != wanted["bytes"] or digest != wanted["sha256"]:
                        raise RuntimeError("mapped training instructions differ from their pinned native window")
                    item["matches"] = True
                record["mapped_training_instructions_verified"] = True
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
        if args.profile == "radial-training":
            record["training_qualification"] = training_qualification(record)
            record["training_qualified"] = record["training_qualification"]["qualified"]
        args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items() if key not in ("messages", "host")}))
    return int("exception" in record or "detach_exception" in record or "script_unload_exception" in record or "preparation_cleanup_exception" in record or "statistics_exception" in record or bool(record["script_errors"]) or record["messages_dropped"] != 0 or record.get("producer_statistics", {}).get("dropped", 0) != 0 or (args.profile == "radial-training" and not record.get("training_qualified", False)))


if __name__ == "__main__":
    raise SystemExit(main())
