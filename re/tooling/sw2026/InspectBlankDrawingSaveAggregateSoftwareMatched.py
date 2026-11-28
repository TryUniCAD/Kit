from __future__ import annotations

import argparse
from functools import partial
import json
import os
from pathlib import Path
import sys

import InspectBlankDrawingSaveAggregate as aggregate
import InspectBlankDrawingSaveEventState as states
import InspectBlankDrawingSaveEvents as events


SCHEMA = "kit.sw2026.blank-drawing-save-aggregate-software-matched.v1"
RESULTS = "DrawingSaveAggregateSoftwareMatchedResults"
RECEIPT = "DrawingBlankSaveAggregateSoftwareMatchedResults.json"
CASE_DIGESTS = {
    "Pristine": "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b",
    "ReducedNative": "3f46a89565adcc7bdf2ed0d8d84c02a085ed47a2ce0d6b1d7b1e235b14e94214",
    "Generated": "ab2b76a87f11344b9172a23ce88985ec8fa4aa98518d1d21597d6dfb1e2c6eeb",
}
ORACLE_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
ANCESTOR_PACKET_SHA256 = "f0490fe9a9125a00a1825c2e3f1cb67fc08729e58a899b42c9fa00ed1fb0d71c"
QUALIFIED_CONTROL_RECEIPT_SHA256 = "e5bd6c5fe6349594bcdf21f0087132adf3e756a6e8c63a7b7fc2d9a78fc9478f"
QUALIFIED_CONTROL_HOST_SHA256 = "d099996fada09b5702df89079683abae1be82f45846496fbd3c0eb4c6f001568"
SOURCE_STATE_PACKET_SHA256 = "63d68733f3e7f28732f7b927c7d0044da38829ce5ba5eeb124cf7d4b1c189455"
SOURCE_STATE_RECEIPT_SHA256 = "cbd2ee083fdf09acee702e1c0e6192ab0f21c44e0731a5a2ff40284bcd3621b7"
EXPECTED_GENERATED_FOOTPRINT = {
    "event_ordinals": [7],
    "save_status": [False, 1, 0],
    "target_states": [
        {"exists": False, "bytes": None},
        {"exists": False, "bytes": None},
        {"exists": True, "bytes": 0},
    ],
}
BACKEND = "dbgeng_managed_software"
ENGINE_DIGESTS = {
    "dbgcore.dll": "de03ffb6b1181434c3db61e7ac63e3383b5732ac8a7d28579a30ff306ef8b8c4",
    "dbgeng.dll": "5a2a515f6263c66b0323d8707abf4b64511a9a34f1f1d3fb1f3c4c17f0bf9cad",
    "dbghelp.dll": "ed7323e007e863dd71e7b405e587969f37e5a146bb0fbcbf885031176bce401d",
    "dbgmodel.dll": "313c4d4b0f0fe4a23f0a8979c83ff40e095828adb4908e1c8869991aefbe6ac9",
    "msdia140.dll": "3499cf0bf1ee71ee04c197c9376fa8438964b557fc172a861572cae21abacd36"
}
TOOLS = frozenset((*events.TOOLS, "InspectBlankDrawingSaveEventState.py", *aggregate.OBSERVER_FILES,
                   "InspectBlankDrawingSaveAggregateSoftwareMatched.py"))


def read_packet(packet, packet_sha):
    require = aggregate.engine.require
    require(events.curves.digest(packet) == packet_sha, "matched aggregate packet differs from its pinned hash")
    job = json.loads(packet.read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE_SHA256
            and job["native_acceptance"] is False and job["heldout_inputs_tested"] == job["writer_output_count"] == 0
            and job["ancestor_packet_sha256"] == ANCESTOR_PACKET_SHA256
            and job["qualified_control_receipt_sha256"] == QUALIFIED_CONTROL_RECEIPT_SHA256
            and job["qualified_control_host_sha256"] == QUALIFIED_CONTROL_HOST_SHA256
            and job["source_state_packet_sha256"] == SOURCE_STATE_PACKET_SHA256
            and job["source_state_receipt_sha256"] == SOURCE_STATE_RECEIPT_SHA256
            and job["expected_generated_footprint"] == EXPECTED_GENERATED_FOOTPRINT
            and job["trace_backend"] == BACKEND,
            "unexpected matched aggregate packet")
    require(job["tool_hashes"]["DrawingSaveAggregateDbgEng.py"] == "e457e00853168e405febf430ff876e6faf4fc4a774c891e6c739760010c09d5c"
            and job["tool_hashes"]["InspectBlankDrawingSaveAggregate.py"] == "b62865a6de7d9fd953655eda473b59f4bb4cd82f84585dfdfb9fba05208f3722",
            "matched primary trace requires the qualified observer bytes")
    rows = job["cases"]
    require(tuple(row["name"] for row in rows) == tuple(CASE_DIGESTS), "expected the three pinned blank inputs")
    require(set(job["tool_hashes"]) == TOOLS, "unexpected matched aggregate tool list")
    for name, expected in job["tool_hashes"].items():
        require(events.curves.digest(Path(__file__).with_name(name)) == expected, f"{name} differs from the packet")
    for row in rows:
        path = events.input_path(packet.parent, row)
        require(row["sha256"] == CASE_DIGESTS[row["name"]] and row["expected"]["view"] is None
                and path.stat().st_size == row["bytes"] and events.curves.digest(path) == row["sha256"],
                "input differs from the frozen blank")
    require(job["stop"] == aggregate.STOP and job["dbgeng_nupkg_sha256"] == aggregate.PACKAGE_SHA256,
            "unexpected debugger package or save stop")
    require(job["amd64_engine_sha256"] == ENGINE_DIGESTS, "unexpected AMD64 engine digests")
    for name, expected in job["amd64_engine_sha256"].items():
        aggregate.engine.check_amd64_image(packet.parent / "Engine" / name, expected)
    return job


def qualified_lane(row):
    trace = (row.get("save_aggregate_trace") if row else None) or {}
    sample = aggregate.qualified_sample(row)
    clock = [trace.get(key) for key in (
        "resume_requested_offset_ns", "save_wait_started_offset_ns", "save_entered_offset_ns",
        "event7_offset_ns", "save_wait_ended_offset_ns", "save_returned_offset_ns",
    )]
    ordered = None not in clock and clock == sorted(clock)
    accepted = (
        sample is not None and ordered and trace.get("breakpoint_kind") == BACKEND
        and trace.get("wait_exit_reason") == "debug_event"
        and trace.get("initial_break_option_verified") and trace.get("initial_stop_verified")
        and trace.get("process_options_verified") and trace.get("detach_method")
        and trace.get("owned_process_debugger_present_after_cleanup") is False
    )
    return sample if accepted else None


def generated_failure(row):
    if row is None or row["save_event_trace"] is None:
        return False
    opened = row["open_and_save"]
    listener_returns = [item["return_value"] for item in states.synchronous_event7(row["save_event_trace"])]
    return bool(
        states.footprint(row) == EXPECTED_GENERATED_FOOTPRINT
        and opened.get("open_errors") == opened.get("open_warnings") == 0
        and opened.get("initial") and opened.get("rebuilt")
        and not opened.get("dialogs") and not opened.get("controller_diagnostics")
        and opened.get("staged_copy_sha256_after") == row["input_sha256"]
        and row["fresh_reopen"] is None and listener_returns == [0]
    )


def evaluate(report):
    lanes = report["lanes"]
    controls = (lanes.get("ControlBefore"), lanes.get("ReducedNative"), lanes.get("ControlAfter"))
    healthy = all(aggregate.native_control(row) for row in controls)
    control_sample = qualified_lane(lanes.get("ReducedNative"))
    generated = lanes.get("Generated")
    generated_sample = qualified_lane(generated)
    identities = states.process_identities(lanes.values())
    distinct = len(set(identities) - {None})
    paths = {(row["matched_input"], row["matched_save"]) for row in lanes.values()}
    reproduced = generated_failure(generated)
    qualified = bool(
        healthy and distinct == len(identities) == 7 and len(paths) == 1 and control_sample == 0
        and generated_sample is not None and reproduced and report["inputs_immutable"]
        and report["last_debugger_cleanup_confirmed"]
        and "exception" not in report and "control_after_exception" not in report
    )
    report.update(
        controls_healthy=healthy,
        distinct_processes=distinct,
        same_physical_paths=len(paths) == 1,
        control_software_sample=control_sample,
        control_software_stop_qualified=bool(aggregate.native_control(controls[1]) and control_sample == 0),
        generated_software_sample=generated_sample,
        generated_wait_exit_reason=((generated or {}).get("save_aggregate_trace") or {}).get("wait_exit_reason"),
        generated_failure_reproduced=reproduced,
        native_aggregate_measurement_qualified=qualified,
        generated_nonzero_aggregate_edge=(generated_sample != 0) if qualified else None,
        generated_footprint=states.footprint(generated),
    )


def run(packet, packet_sha):
    job = read_packet(packet, packet_sha)
    engine = aggregate.engine
    engine.require(os.name == "nt" and engine.pe_machine(Path(sys.executable).read_bytes()) == engine.AMD64,
                   "the matched aggregate observer requires AMD64 Windows Python")
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / RESULTS
    output.mkdir(exist_ok=False)
    cleanup = {"confirmed": True}
    report = {
        "schema": SCHEMA,
        "packet_sha256": packet_sha,
        "observer_tool_sha256": {name: job["tool_hashes"][name] for name in (*aggregate.OBSERVER_FILES, Path(__file__).name)},
        "dbgeng_nupkg_sha256": job["dbgeng_nupkg_sha256"],
        "source_state_packet_sha256": job["source_state_packet_sha256"],
        "ancestor_packet_sha256": ANCESTOR_PACKET_SHA256,
        "qualified_control_receipt_sha256": QUALIFIED_CONTROL_RECEIPT_SHA256,
        "qualified_control_host_sha256": QUALIFIED_CONTROL_HOST_SHA256,
        "source_state_receipt_sha256": SOURCE_STATE_RECEIPT_SHA256,
        "trace_backend": BACKEND,
        "native_acceptance": False,
        "writer_output_count": 0,
        "heldout_inputs_tested": 0,
        "generated_attempted": False,
        "lanes": {},
    }
    pristine, reduced, generated = job["cases"]

    def measure(label, case, tree, *, debug=False):
        previous_observer, previous_events = events.observe_operation, events.EVENTS
        if debug:
            events.observe_operation = partial(aggregate.observe_aggregate, engine_path=packet.parent / "Engine" / "dbgeng.dll",
                                               oracle_hash=job["oracle_sha256"], identify=application_identity, cleanup=cleanup)
        else:
            events.observe_operation = partial(states.observe_operation, event7_return=0)
        events.EVENTS = previous_events | frozenset(states.AUTOSAVE_HANDLERS)
        try:
            row = events.run_lane(Swapp, application_identity, packet=packet, row=case, oracle=job["oracle_sha256"],
                                  label=label, output=output, tree=tree)
        finally:
            events.observe_operation, events.EVENTS = previous_observer, previous_events
        phase = output / label / "open_and_save" / "Record.json"
        row["save_aggregate_trace"] = json.loads(phase.read_bytes()).get("save_aggregate_trace")
        report["lanes"][label] = row
        report["last_debugger_cleanup_confirmed"] = cleanup["confirmed"]
        events.curves.write_json(output / "Progress.json", report)
        return row

    tree = None
    try:
        before = measure("ControlBefore", pristine, None)
        if aggregate.native_control(before):
            tree = before["open_and_save"]["tree"]
            native = measure("ReducedNative", reduced, tree, debug=True)
            if cleanup["confirmed"] and aggregate.native_control(native) and qualified_lane(native) == 0:
                report["generated_attempted"] = True
                measure("Generated", generated, generated["expected_tree"], debug=True)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        if cleanup["confirmed"]:
            try:
                interrupted = output / "MatchedDrawing"
                if interrupted.exists():
                    interrupted.rename(output / "InterruptedLane")
                measure("ControlAfter", pristine, tree)
            except Exception as error:
                report["control_after_exception"] = repr(error)
    read_packet(packet, packet_sha)
    report["inputs_immutable"] = True
    report["last_debugger_cleanup_confirmed"] = cleanup["confirmed"]
    evaluate(report)
    events.curves.write_json(output / RECEIPT, report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Read the listener aggregate in matched native and generated drawing saves")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    packet = arguments.packet.resolve()
    if arguments.verify_only:
        read_packet(packet, arguments.packet_sha256)
        print(json.dumps({"packet_sha256": arguments.packet_sha256, "custody_verified": True}))
        return 0
    result = run(packet, arguments.packet_sha256)
    keys = ("control_software_stop_qualified", "control_software_sample", "generated_software_sample",
            "native_aggregate_measurement_qualified", "generated_failure_reproduced", "generated_nonzero_aggregate_edge",
            "generated_wait_exit_reason", "last_debugger_cleanup_confirmed", "distinct_processes")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["native_aggregate_measurement_qualified"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
