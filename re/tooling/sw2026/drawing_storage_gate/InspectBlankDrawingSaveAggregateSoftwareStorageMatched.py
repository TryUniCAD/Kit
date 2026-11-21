from __future__ import annotations

import argparse
from functools import partial
import json
import os
from pathlib import Path
import sys

import DrawingSaveStorageGateDbgEng as storage
import InspectBlankDrawingSaveAggregate as aggregate
import InspectBlankDrawingSaveAggregateSoftwareReturnMatched as returns
import InspectBlankDrawingSaveEventState as states
import InspectBlankDrawingSaveEvents as events


SCHEMA = "kit.sw2026.blank-drawing-save-storage-matched.v1"
RESULTS = "DrawingSaveAggregateSoftwareStorageMatchedResults"
RECEIPT = "DrawingBlankSaveAggregateSoftwareStorageMatchedResults.json"
SOURCE_PACKET_SHA256 = "b51a5bf1f07da16b5e8607499662b13f7fbaa237dd7fc5519af9a7d1a7f93500"
SOURCE_RECEIPT_SHA256 = "b8194deeddc4ce24ebdc376fd1040c6d175f79eed23949fd4937ad7e3001df81"
SOURCE_HOST_SHA256 = "d8a5e84088d83cd6a3f261e62e06af2719343922c3ee34ede7bac3df3571ff1d"
TOOLS = ("DrawingSaveStorageGateDbgEng.py", "InspectBlankDrawingSaveAggregateSoftwareStorageMatched.py")
OBSERVED = "observed"
UNSEEN = "save_returned_with_stop_unobserved"
UNQUALIFIED = "unqualified"


def read_packet(packet, digest):
    require = aggregate.engine.require
    require(events.curves.digest(packet) == digest, "storage packet differs from its pinned hash")
    job = json.loads(packet.read_bytes())
    require(job["schema"] == SCHEMA and job["source_return_packet_sha256"] == SOURCE_PACKET_SHA256
            and job["source_return_receipt_sha256"] == SOURCE_RECEIPT_SHA256
            and job["source_return_host_sha256"] == SOURCE_HOST_SHA256
            and job["storage_stops"] == list(storage.STORAGE_STOPS)
            and job["native_acceptance"] is False and job["heldout_inputs_tested"] == 0
            and job["writer_output_count"] == 0 and set(job["tool_hashes"]) == set(TOOLS),
            "unexpected matched storage packet")
    for name, expected in job["tool_hashes"].items():
        require(events.curves.digest(Path(__file__).with_name(name)) == expected, f"{name} differs from the packet")
    source = returns.read_packet(packet.with_name("SourceTrial.json"), SOURCE_PACKET_SHA256)
    return job, source


def stage_summary(trace, stage, *, expected_rva, previous_stop_end, require_eax=False):
    reason = stage.get("wait_exit_reason")
    sample = stage.get("sample")
    eax = sample.get("eax_signed") if sample else None
    result = {"state": UNQUALIFIED, "wait_exit_reason": reason, "eax_signed": None, "eax_hex": None}
    if (stage.get("rva") != expected_rva or not stage.get("prior_breakpoint_removed")
            or not stage.get("armed") or stage.get("wait_calls", 0) < 1):
        return result

    start = [previous_stop_end, stage.get("resume_requested_offset_ns"), stage.get("save_wait_started_offset_ns")]
    completed = trace.get("save_returned_offset_ns")
    observed = [*start, stage.get("save_wait_ended_offset_ns"), completed]
    sample_ok = (
        sample and sample.get("same_save_thread") and sample.get("nested_save_frame")
        and sample.get("effective_processor") == hex(aggregate.engine.AMD64)
        and sample.get("executing_processor") == hex(aggregate.engine.AMD64)
    )
    typed_eax = (type(eax) is int and -(1 << 31) <= eax < (1 << 31)
                 and sample.get("eax_hex") == f"0x{eax & 0xFFFFFFFF:08x}")
    if (reason == "debug_event" and sample_ok and (not require_eax or typed_eax)
            and None not in observed and observed == sorted(observed)):
        result["state"] = OBSERVED
        if require_eax:
            result.update(eax_signed=eax, eax_hex=sample["eax_hex"])
    returned = [*start, completed, stage.get("save_wait_ended_offset_ns")]
    if (reason == "save_returned" and sample is None and stage.get("timed_out_wait_calls", 0) > 0
            and None not in returned and returned == sorted(returned)):
        result["state"] = UNSEEN
    return result


def storage_trace(row):
    trace = (row or {}).get("save_aggregate_trace") or {}
    path = trace.get("storage_path") or {}
    entry = path.get("save_doc_entry") or {}
    validity = path.get("storage_root_validity") or {}
    if returns.qualified_lane(row) != 0:
        return {"route": UNQUALIFIED, "entry": None, "validity": None}

    entry_status = stage_summary(trace, entry, expected_rva=storage.SAVE_DOC_ENTRY_RVA,
                                 previous_stop_end=trace.get("save_wait_ended_offset_ns"))
    result = {"route": UNQUALIFIED, "entry": entry_status, "validity": None}
    if entry_status["state"] == UNSEEN and not validity:
        result["route"] = "storage_save_entry_unobserved"
    if entry_status["state"] == OBSERVED:
        root = stage_summary(trace, validity, expected_rva=storage.ROOT_VALIDITY_RVA,
                             previous_stop_end=entry.get("save_wait_ended_offset_ns"), require_eax=True)
        result["validity"] = root
        if root["state"] == OBSERVED:
            result["route"] = "root_valid" if root["eax_signed"] else "root_invalid"
        if root["state"] == UNSEEN:
            result["route"] = "root_validity_unobserved"
    return result


def observe_storage(*args, **kwargs):
    original = aggregate.engine.SaveAggregateTrace
    aggregate.engine.require(original is storage.StorageGateTrace.__base__, "unexpected prior debugger observer")
    aggregate.engine.SaveAggregateTrace = storage.StorageGateTrace
    try:
        return aggregate.observe_aggregate(*args, **kwargs)
    finally:
        aggregate.engine.SaveAggregateTrace = original


def evaluate(report):
    lanes = report["lanes"]
    before, reduced, generated, after = (lanes.get(key) for key in ("ControlBefore", "ReducedNative", "Generated", "ControlAfter"))
    healthy = all(aggregate.native_control(row) for row in (before, reduced, after))
    control_trace = storage_trace(reduced)
    candidate_trace = storage_trace(generated)
    identities = states.process_identities(lanes.values())
    distinct = len(set(identities) - {None})
    paths = {(row["matched_input"], row["matched_save"]) for row in lanes.values()}
    reproduced = returns.generated_failure(generated)
    qualified = bool(
        healthy and distinct == len(identities) == 7 and len(paths) == 1 and reproduced
        and control_trace["route"] == "root_valid" and candidate_trace["route"] != UNQUALIFIED
        and report["inputs_immutable"] and report["last_debugger_cleanup_confirmed"]
        and "exception" not in report and "control_after_exception" not in report
    )
    report.update(
        storage_route_comparison_qualified=qualified,
        control_storage_trace=control_trace,
        generated_storage_trace=candidate_trace,
        controls_healthy=healthy,
        distinct_processes=distinct,
        same_physical_paths=len(paths) == 1,
        control_listener_aggregate=returns.qualified_lane(reduced),
        generated_listener_aggregate=returns.qualified_lane(generated),
        generated_failure_reproduced=reproduced,
        generated_footprint=states.footprint(generated),
    )


def run(packet, digest):
    job, source = read_packet(packet, digest)
    engine = aggregate.engine
    engine.require(os.name == "nt" and engine.pe_machine(Path(sys.executable).read_bytes()) == engine.AMD64,
                   "the storage observer requires AMD64 Windows Python")
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / RESULTS
    output.mkdir(exist_ok=False)
    cleanup = {"confirmed": True}
    report = {
        "schema": SCHEMA,
        "packet_sha256": digest,
        "source_return_packet_sha256": SOURCE_PACKET_SHA256,
        "source_return_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "source_return_host_sha256": SOURCE_HOST_SHA256,
        "storage_stops": job["storage_stops"],
        "observer_tool_sha256": {**{name: source["tool_hashes"][name] for name in aggregate.OBSERVER_FILES},
                                 **job["tool_hashes"]},
        "native_acceptance": False,
        "writer_output_count": 0,
        "heldout_inputs_tested": 0,
        "generated_attempted": False,
        "lanes": {},
    }
    pristine, reduced, generated = source["cases"]

    def measure(label, case, tree, *, debug=False):
        previous_observer, previous_events = events.observe_operation, events.EVENTS
        if debug:
            events.observe_operation = partial(observe_storage, engine_path=packet.parent / "Engine" / "dbgeng.dll",
                                               oracle_hash=source["oracle_sha256"], identify=application_identity,
                                               cleanup=cleanup)
        else:
            events.observe_operation = partial(states.observe_operation, event7_return=0)
        events.EVENTS = previous_events | frozenset(states.AUTOSAVE_HANDLERS)
        try:
            row = events.run_lane(Swapp, application_identity, packet=packet, row=case, oracle=source["oracle_sha256"],
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
            if cleanup["confirmed"] and aggregate.native_control(native) and storage_trace(native)["route"] == "root_valid":
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
    read_packet(packet, digest)
    report["inputs_immutable"] = True
    report["last_debugger_cleanup_confirmed"] = cleanup["confirmed"]
    evaluate(report)
    events.curves.write_json(output / RECEIPT, report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Trace the matched drawing storage save entry and root validity")
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
    keys = ("storage_route_comparison_qualified", "control_storage_trace", "generated_storage_trace",
            "controls_healthy", "distinct_processes", "generated_failure_reproduced", "last_debugger_cleanup_confirmed")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["storage_route_comparison_qualified"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
