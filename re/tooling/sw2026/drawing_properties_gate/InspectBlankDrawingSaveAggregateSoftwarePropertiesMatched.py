from __future__ import annotations

import argparse
from functools import partial
import json
import os
from pathlib import Path
import sys

import DrawingSavePropertiesGateDbgEng as properties
import InspectBlankDrawingSaveAggregate as aggregate
import InspectBlankDrawingSaveAggregateSoftwarePreviewMatched as preview
import InspectBlankDrawingSaveAggregateSoftwareStorageMatched as storage
import InspectBlankDrawingSaveEventState as states
import InspectBlankDrawingSaveEvents as events


SCHEMA = "kit.sw2026.blank-drawing-save-properties-matched.v1"
RESULTS = "DrawingSaveAggregateSoftwarePropertiesMatchedResults"
RECEIPT = "DrawingBlankSaveAggregateSoftwarePropertiesMatchedResults.json"
SOURCE_PACKET_SHA256 = "4cae8865822b4f37f2f7128c9c8ccda41d4ef202b81b6bb56f561ce85ba9d92d"
SOURCE_RECEIPT_SHA256 = "d9dfcacb95056b49747c230b41975d1fc8b73176ef774920f98cb181280dc6fd"
SOURCE_HOST_SHA256 = "4459175bced81a4267623159990974a4779387b48bb69a92463861a9b42b44e6"
TOOLS = ("DrawingSavePropertiesGateDbgEng.py", "InspectBlankDrawingSaveAggregateSoftwarePropertiesMatched.py")
UNQUALIFIED = storage.UNQUALIFIED
UNSEEN = storage.UNSEEN
OBSERVED = storage.OBSERVED


def read_packet(packet, digest):
    require = aggregate.engine.require
    require(events.curves.digest(packet) == digest, "properties packet differs from its pinned hash")
    job = json.loads(packet.read_bytes())
    require(job["schema"] == SCHEMA and job["source_preview_packet_sha256"] == SOURCE_PACKET_SHA256
            and job["source_preview_receipt_sha256"] == SOURCE_RECEIPT_SHA256
            and job["source_preview_host_sha256"] == SOURCE_HOST_SHA256
            and job["source_preview_full_comparison_qualified"] is False
            and job["properties_stops"] == list(properties.PROPERTIES_STOPS)
            and job["dbgeng_sdk_header_sha256"] == properties.SDK_HEADER_SHA256
            and job["native_acceptance"] is False and job["heldout_inputs_tested"] == 0
            and job["writer_output_count"] == 0 and set(job["tool_hashes"]) == set(TOOLS),
            "unexpected matched properties packet")
    for name, expected in job["tool_hashes"].items():
        require(events.curves.digest(Path(__file__).with_name(name)) == expected, f"{name} differs from the packet")
    prior, earlier, source = preview.read_packet(packet.with_name("SourcePreviewTrial.json"), SOURCE_PACKET_SHA256)
    return job, prior, earlier, source


def cleanup_qualified(trace):
    audit = trace.get("breakpoint_cleanup") or {}
    sites = trace.get("breakpoint_sites") or []
    rvas = [row.get("rva") for row in sites]
    expected = [aggregate.engine.STOP_RVA, properties.AFTER_PROPERTIES_RVA, properties.THIRD_PARTY_RVA]
    if (not sites or rvas not in (expected[:2], expected)
            or not audit.get("qualified") or not audit.get("detached_and_restored")
            or not audit.get("before_detach_read_complete") or not audit.get("after_detach_read_complete")
            or not audit.get("all_sites_original_after_detach")
            or trace.get("owned_process_debugger_present_after_cleanup") is not False
            or not trace.get("cleanup_confirmed") or not trace.get("detach_method")):
        return False
    for site in sites:
        expected_hash = site.get("original_sha256")
        before = site.get("before_detach") or {}
        after = site.get("after_detach") or {}
        if (not site.get("armed") or site.get("bytes") != 1 or not site.get("before_arm_matches_original")
                or not isinstance(expected_hash, str) or len(expected_hash) != 64
                or site.get("before_arm_sha256") != expected_hash
                or before.get("bytes_read") != 1 or after.get("bytes_read") != 1
                or not after.get("matches_original") or after.get("sha256") != expected_hash):
            return False
    explicit = bool(trace.get("breakpoint_removed") and all(site.get("remove_call_succeeded") for site in sites))
    if audit.get("explicit_removal_complete") is not explicit:
        return False
    return audit.get("mode") == ("explicit_removed" if explicit else "detached_restored")


def qualified_lane(row):
    trace = (row or {}).get("save_aggregate_trace") or {}
    sample = trace.get("sample") or {}
    clock = [trace.get(key) for key in (
        "resume_requested_offset_ns", "save_wait_started_offset_ns", "save_entered_offset_ns",
        "event7_offset_ns", "save_wait_ended_offset_ns", "save_returned_offset_ns",
    )]
    if (not trace.get("armed") or trace.get("failure") is not None or not cleanup_qualified(trace)
            or trace.get("breakpoint_kind") != "dbgeng_managed_software"
            or trace.get("wait_exit_reason") != "debug_event"
            or not trace.get("initial_break_option_verified") or not trace.get("initial_stop_verified")
            or not trace.get("process_options_verified") or None in clock or clock != sorted(clock)):
        return None
    if (sample.get("rva"), sample.get("effective_processor"), sample.get("executing_processor"),
            sample.get("bytes_read"), sample.get("event7_seen")) != (
        aggregate.engine.STOP_RVA, hex(aggregate.engine.AMD64), hex(aggregate.engine.AMD64),
        aggregate.engine.SAMPLE_BYTES, True,
    ):
        return None
    return sample.get("aggregate")


def properties_trace(row):
    trace = (row or {}).get("save_aggregate_trace") or {}
    path = trace.get("properties_path") or {}
    result = {"route": UNQUALIFIED, "after_document_properties": None, "third_party_dispatch": None}
    if qualified_lane(row) != 0:
        return result
    stages = (
        ("after_document_properties", properties.AFTER_PROPERTIES_RVA, "established"),
        ("third_party_dispatch", properties.THIRD_PARTY_RVA, "same_as_first_getter"),
    )
    expected_names = set()
    prior_end = trace.get("save_wait_ended_offset_ns")
    for name, rva, frame in stages:
        expected_names.add(name)
        stage = path.get(name) or {}
        summary = storage.stage_summary(trace, stage, expected_rva=rva, previous_stop_end=prior_end)
        result[name] = summary
        if summary["state"] == UNQUALIFIED:
            return result
        if summary["state"] == UNSEEN:
            if set(path) == expected_names:
                result["route"] = f"{name}_unobserved"
            return result
        if stage["sample"].get("storage_frame_relation") != frame:
            return result
        prior_end = stage.get("save_wait_ended_offset_ns")
    if set(path) == expected_names:
        result["route"] = "third_party_dispatch_observed"
    return result


def observe_properties(*args, **kwargs):
    original = aggregate.engine.SaveAggregateTrace
    aggregate.engine.require(original is properties.preview.PreviewGateTrace.__base__,
                             "unexpected prior debugger observer")
    aggregate.engine.SaveAggregateTrace = properties.PropertiesGateTrace
    try:
        return aggregate.observe_aggregate(*args, **kwargs)
    finally:
        aggregate.engine.SaveAggregateTrace = original


def evaluate(report):
    lanes = report["lanes"]
    before, reduced, generated, after = (lanes.get(key) for key in ("ControlBefore", "ReducedNative", "Generated", "ControlAfter"))
    healthy = all(aggregate.native_control(row) for row in (before, reduced, after))
    native_trace = properties_trace(reduced)
    candidate_trace = properties_trace(generated)
    identities = states.process_identities(lanes.values())
    distinct = len(set(identities) - {None})
    paths = {(row["matched_input"], row["matched_save"]) for row in lanes.values()}
    reproduced = preview.returns.generated_failure(generated)
    qualified = bool(
        healthy and distinct == len(identities) == 7 and len(paths) == 1 and reproduced
        and native_trace["route"] == "third_party_dispatch_observed" and candidate_trace["route"] != UNQUALIFIED
        and report["inputs_immutable"] and report["last_debugger_cleanup_confirmed"]
        and "exception" not in report and "control_after_exception" not in report
    )
    native_debugger = (reduced or {}).get("save_aggregate_trace") or {}
    candidate_debugger = (generated or {}).get("save_aggregate_trace") or {}
    report.update(
        properties_route_comparison_qualified=qualified,
        control_properties_trace=native_trace,
        generated_properties_trace=candidate_trace,
        controls_healthy=healthy,
        distinct_processes=distinct,
        same_physical_paths=len(paths) == 1,
        control_listener_aggregate=qualified_lane(reduced),
        generated_listener_aggregate=qualified_lane(generated),
        generated_failure_reproduced=reproduced,
        generated_footprint=states.footprint(generated),
        control_cleanup=native_debugger.get("breakpoint_cleanup"),
        generated_cleanup=candidate_debugger.get("breakpoint_cleanup"),
    )


def run(packet, digest):
    job, prior, earlier, source = read_packet(packet, digest)
    engine = aggregate.engine
    engine.require(os.name == "nt" and engine.pe_machine(Path(sys.executable).read_bytes()) == engine.AMD64,
                   "the properties observer requires AMD64 Windows Python")
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / RESULTS
    output.mkdir(exist_ok=False)
    cleanup = {"confirmed": True}
    report = {
        "schema": SCHEMA,
        "packet_sha256": digest,
        "source_preview_packet_sha256": SOURCE_PACKET_SHA256,
        "source_preview_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "source_preview_host_sha256": SOURCE_HOST_SHA256,
        "source_preview_full_comparison_qualified": False,
        "properties_stops": job["properties_stops"],
        "dbgeng_sdk_header_sha256": job["dbgeng_sdk_header_sha256"],
        "observer_tool_sha256": {**source["tool_hashes"], **earlier["tool_hashes"],
                                 **prior["tool_hashes"], **job["tool_hashes"]},
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
            events.observe_operation = partial(observe_properties, engine_path=packet.parent / "Engine" / "dbgeng.dll",
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
            if (cleanup["confirmed"] and aggregate.native_control(native)
                    and properties_trace(native)["route"] == "third_party_dispatch_observed"):
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
    parser = argparse.ArgumentParser(description="Trace document-property save completion and third-party dispatch")
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
    keys = ("properties_route_comparison_qualified", "control_properties_trace", "generated_properties_trace",
            "control_cleanup", "generated_cleanup", "controls_healthy", "distinct_processes",
            "generated_failure_reproduced", "last_debugger_cleanup_confirmed")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["properties_route_comparison_qualified"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
