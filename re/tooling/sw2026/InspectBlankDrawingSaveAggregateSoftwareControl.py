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


SCHEMA = "kit.sw2026.blank-drawing-save-aggregate-software-control.v1"
RESULTS = "DrawingSaveAggregateSoftwareControlResults"
RECEIPT = "DrawingBlankSaveAggregateSoftwareControlResults.json"
CASE_DIGESTS = {
    "Pristine": "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b",
    "ReducedNative": "3f46a89565adcc7bdf2ed0d8d84c02a085ed47a2ce0d6b1d7b1e235b14e94214",
}
ORACLE_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
ANCESTOR_PACKET_SHA256 = "36b99474ee59539c1aeb53fef3420d35bebaf2cefdbba814e1398c3ebd886cd6"
RETRY_REASON_RECEIPT_SHA256 = "a7ffc0a65fdcc8668010b422f4f32dc7d75945029a8333c21389f56355ce241a"
BACKEND = "dbgeng_managed_software"
ENGINE_DIGESTS = {
    "dbgcore.dll": "de03ffb6b1181434c3db61e7ac63e3383b5732ac8a7d28579a30ff306ef8b8c4",
    "dbgeng.dll": "5a2a515f6263c66b0323d8707abf4b64511a9a34f1f1d3fb1f3c4c17f0bf9cad",
    "dbghelp.dll": "ed7323e007e863dd71e7b405e587969f37e5a146bb0fbcbf885031176bce401d",
    "dbgmodel.dll": "313c4d4b0f0fe4a23f0a8979c83ff40e095828adb4908e1c8869991aefbe6ac9",
    "msdia140.dll": "3499cf0bf1ee71ee04c197c9376fa8438964b557fc172a861572cae21abacd36"
}
TOOLS = frozenset((*events.TOOLS, "InspectBlankDrawingSaveEventState.py", *aggregate.OBSERVER_FILES,
                   "InspectBlankDrawingSaveAggregateSoftwareControl.py"))


def read_packet(packet, packet_sha):
    require = aggregate.engine.require
    require(events.curves.digest(packet) == packet_sha, "control-only packet differs from its pinned hash")
    job = json.loads(packet.read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE_SHA256
            and job["native_acceptance"] is False and job["heldout_inputs_tested"] == job["writer_output_count"] == 0
            and job["ancestor_packet_sha256"] == ANCESTOR_PACKET_SHA256
            and job["retry_reason_receipt_sha256"] == RETRY_REASON_RECEIPT_SHA256
            and job["trace_backend"] == BACKEND,
            "unexpected control-only packet")
    rows = job["cases"]
    require(tuple(row["name"] for row in rows) == tuple(CASE_DIGESTS), "expected only pristine and reduced-native inputs")
    require(set(job["tool_hashes"]) == TOOLS, "unexpected control-only tool list")
    for name, expected in job["tool_hashes"].items():
        require(events.curves.digest(Path(__file__).with_name(name)) == expected, f"{name} differs from the packet")
    for row in rows:
        path = events.input_path(packet.parent, row)
        require(row["sha256"] == CASE_DIGESTS[row["name"]] and row["expected"]["view"] is None
                and path.stat().st_size == row["bytes"] and events.curves.digest(path) == row["sha256"],
                "control input differs from the frozen blank")
    require(job["stop"] == aggregate.STOP and job["dbgeng_nupkg_sha256"] == aggregate.PACKAGE_SHA256,
            "unexpected debugger package or save stop")
    require(job["amd64_engine_sha256"] == ENGINE_DIGESTS, "unexpected AMD64 engine digests")
    for name, expected in job["amd64_engine_sha256"].items():
        aggregate.engine.check_amd64_image(packet.parent / "Engine" / name, expected)
    return job


def evaluate(report):
    lanes = report["lanes"]
    ordered = [lanes.get(name) for name in ("ControlBefore", "ReducedNative", "ControlAfter")]
    controls_healthy = all(aggregate.native_control(row) for row in ordered)
    reduced = lanes.get("ReducedNative")
    trace = (reduced.get("save_aggregate_trace") if reduced else None) or {}
    sample = aggregate.qualified_sample(reduced)
    identities = states.process_identities(lanes.values())
    fresh = None not in identities and len(set(identities)) == len(identities) == 6
    paths = {(row["matched_input"], row["matched_save"]) for row in lanes.values()}
    handoff = [trace.get(key) for key in ("resume_requested_offset_ns", "save_wait_started_offset_ns",
                                          "save_entered_offset_ns", "event7_offset_ns",
                                          "save_wait_ended_offset_ns", "save_returned_offset_ns")]
    ordered_handoff = None not in handoff and handoff == sorted(handoff)
    qualified = bool(
        controls_healthy and fresh and len(paths) == 1 and sample == 0 and ordered_handoff
        and trace.get("breakpoint_kind") == BACKEND and trace.get("wait_exit_reason") == "debug_event"
        and trace.get("initial_break_option_verified") and trace.get("initial_stop_verified")
        and trace.get("process_options_verified") and trace.get("detach_method")
        and trace.get("owned_process_debugger_present_after_cleanup") is False
        and report["last_debugger_cleanup_confirmed"]
        and "exception" not in report and "control_after_exception" not in report
    )
    report.update(
        controls_healthy=controls_healthy,
        distinct_processes=len(set(identities) - {None}),
        same_physical_paths=len(paths) == 1,
        initial_break_already_enabled=trace.get("initial_break_already_enabled"),
        initial_break_option_verified=bool(trace.get("initial_break_option_verified")),
        initial_owned_stop_verified=bool(trace.get("initial_stop_verified")),
        control_software_sample=sample,
        wait_saveas_exit_reason=trace.get("wait_exit_reason"),
        wait_and_save_timestamps_ordered=ordered_handoff,
        control_software_stop_qualified=qualified,
        failure_stage=trace.get("failure_stage"),
    )


def run(packet, packet_sha):
    job = read_packet(packet, packet_sha)
    engine = aggregate.engine
    engine.require(os.name == "nt" and engine.pe_machine(Path(sys.executable).read_bytes()) == engine.AMD64,
                   "the control-only aggregate observer requires AMD64 Windows Python")
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
        "retry_reason_receipt_sha256": RETRY_REASON_RECEIPT_SHA256,
        "trace_backend": BACKEND,
        "native_acceptance": False,
        "writer_output_count": 0,
        "heldout_inputs_tested": 0,
        "generated_attempted": False,
        "lanes": {},
    }
    pristine, reduced = job["cases"]

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
            measure("ReducedNative", reduced, tree, debug=True)
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
    parser = argparse.ArgumentParser(description="Qualify the native blank control debugger stop and aggregate sample")
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
    keys = ("control_software_stop_qualified", "initial_break_option_verified", "initial_owned_stop_verified",
            "control_software_sample", "last_debugger_cleanup_confirmed", "failure_stage", "distinct_processes",
            "wait_saveas_exit_reason", "wait_and_save_timestamps_ordered")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["control_software_stop_qualified"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
