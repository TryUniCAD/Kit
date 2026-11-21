from __future__ import annotations

import argparse
from functools import partial
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Ancestor02" / "Tools"))

import DrawingSavePropertyBracketsDbgEng as worker
import InspectBlankDrawingSavePropertyStorageModeMatched as previous
import InspectBlankDrawingSaveAggregateSoftwareReturnMatched as returns
import InspectBlankDrawingSaveAggregate as aggregate
import InspectBlankDrawingSaveAggregateSoftwareStorageMatched as storage
import InspectBlankDrawingSaveEventState as states
import InspectBlankDrawingSaveEvents as events


SCHEMA = "kit.sw2026.blank-drawing-property-brackets-matched.v1"
RESULTS = "DrawingSavePropertyBracketsMatchedResults"
RECEIPT = "DrawingBlankSavePropertyBracketsMatchedResults.json"
SOURCE_PACKET_SHA256 = "0de1f96aa9e9d78e8fb7254847cac35915fd5d6ee6f57316d9ca4c2dac5eb03a"
SOURCE_RECEIPT_SHA256 = "ff967d1e52aa384fb67af62cdbc9fa96124935530c22c1ba05f64c7567301c86"
SOURCE_HOST_SHA256 = "9cc1054d363d8f0cbd8fe9c4caea669be8ed74ab7552b19d851f5691a1c6e101"
CANDIDATE_SHA256 = "7400cf1fa4a71994807ce8e49283e2721e09a5ceaf723e36f6ae807906c94a26"

def read_packet(packet, digest):
    require = aggregate.engine.require
    require(events.curves.digest(packet) == digest, "storage-mode packet differs from its pinned hash")
    job = json.loads(packet.read_bytes())
    require(job["schema"] == SCHEMA and job["source_inside_call_packet_sha256"] == SOURCE_PACKET_SHA256
            and job["source_inside_call_receipt_sha256"] == SOURCE_RECEIPT_SHA256
            and job["source_inside_call_host_sha256"] == SOURCE_HOST_SHA256
            and job["source_inside_call_comparison_qualified"] is True
            and job["stops"] == list(worker.STOPS) and job["module_sha256"] == worker.MODULE_SHA256
            and job["dbgeng_sdk_header_sha256"] == worker.SDK_HEADER_SHA256
            and job["native_acceptance"] is False and job["heldout_inputs_tested"] == 0
            and job["writer_output_count"] == 0, "unexpected fixed property-brackets packet")
    tools = Path(__file__).parent
    require(set(job["tool_hashes"]) == {path.name for path in tools.glob("*.py")}, "unexpected storage-mode tool list")
    for name, expected in job["tool_hashes"].items():
        require(events.curves.digest(tools / name) == expected, f"{name} differs from the packet")
    for name, expected in job["custody_files"].items():
        require(Path(name).name == name and events.curves.digest(packet.parent / name) == expected,
                "frozen custody file differs")
    prior, source = previous.read_packet(packet.parent / "Ancestor02" / "Trial.json", SOURCE_PACKET_SHA256)
    candidate = job["candidate"]
    artifact = events.input_path(packet.parent, candidate)
    require(candidate["name"] == "GeneratedSections" and candidate["sha256"] == CANDIDATE_SHA256
            and artifact.stat().st_size == candidate["bytes"] and events.curves.digest(artifact) == CANDIDATE_SHA256
            and candidate["expected"] == source["cases"][2]["expected"]
            and candidate["expected_tree"] == source["cases"][2]["expected_tree"]
            and candidate == prior["candidate"], "corrected candidate differs")
    for row in (*source["cases"][:2], candidate):
        artifact = events.input_path(packet.parent, row)
        require(artifact.stat().st_size == row["bytes"] and events.curves.digest(artifact) == row["sha256"],
                "matched current-packet input differs")
    return job, source


def cleanup_qualified(trace):
    audit = trace.get("breakpoint_cleanup") or {}
    sites = trace.get("breakpoint_sites") or []
    if (not sites or not audit.get("qualified") or not audit.get("detached_and_restored")
            or not audit.get("before_detach_read_complete") or not audit.get("after_detach_read_complete")
            or not audit.get("all_sites_original_after_detach")
            or trace.get("owned_process_debugger_present_after_cleanup") is not False
            or not trace.get("cleanup_confirmed") or not trace.get("detach_method")):
        return False
    locations = [(site.get("module"), site.get("rva")) for site in sites]
    if locations[0] != ("doccplu.dll", aggregate.engine.STOP_RVA) or len(set(locations)) != len(locations):
        return False
    for site in sites:
        module, rva = site.get("module"), site.get("rva")
        if module not in worker.ALLOWED_RVAS or rva not in worker.ALLOWED_RVAS[module]:
            return False
        expected = site.get("original_sha256")
        before, after = site.get("before_detach") or {}, site.get("after_detach") or {}
        if (not site.get("armed") or site.get("bytes") != 1 or not site.get("before_arm_matches_original")
                or not isinstance(expected, str) or len(expected) != 64 or site.get("before_arm_sha256") != expected
                or before.get("bytes_read") != 1 or after.get("bytes_read") != 1
                or not after.get("matches_original") or after.get("sha256") != expected):
            return False
    explicit = bool(trace.get("breakpoint_removed") and all(site.get("remove_call_succeeded") for site in sites))
    return bool(audit.get("explicit_removal_complete") is explicit
                and audit.get("mode") == ("explicit_removed" if explicit else "detached_restored"))


def qualified_aggregate(row):
    trace = (row or {}).get("save_aggregate_trace") or {}
    sample = trace.get("sample") or {}
    clock = [trace.get(key) for key in ("resume_requested_offset_ns", "save_wait_started_offset_ns", "save_entered_offset_ns",
                                       "event7_offset_ns", "save_wait_ended_offset_ns", "save_returned_offset_ns")]
    return bool(trace.get("armed") and trace.get("failure") is None and cleanup_qualified(trace)
                and trace.get("breakpoint_kind") == "dbgeng_managed_software" and trace.get("wait_exit_reason") == "debug_event"
                and trace.get("initial_break_option_verified") and trace.get("initial_stop_verified")
                and trace.get("process_options_verified") and None not in clock and clock == sorted(clock)
                and (sample.get("rva"), sample.get("effective_processor"), sample.get("executing_processor"),
                     sample.get("bytes_read"), sample.get("event7_seen"), sample.get("aggregate")) == (
                    aggregate.engine.STOP_RVA, hex(aggregate.engine.AMD64), hex(aggregate.engine.AMD64),
                    aggregate.engine.SAMPLE_BYTES, True, 0))


def storage_trace(row):
    trace = (row or {}).get("save_aggregate_trace") or {}
    path = trace.get("property_brackets_path") or {}
    result = {"route": storage.UNQUALIFIED, "stages": {}}
    if not qualified_aggregate(row):
        return result
    prior_end = trace.get("save_wait_ended_offset_ns")
    expected_names = []
    for index, spec in enumerate(worker.STOPS):
        name, rva = spec["name"], spec["instruction_rva"]
        expected_names.append(name)
        raw = path.get(name) or {}
        summary = storage.stage_summary(trace, raw, expected_rva=rva, previous_stop_end=prior_end,
                                        require_eax=spec["sample"] == "signed_eax")
        result["stages"][name] = summary
        if raw.get("module") != spec["module"]:
            return result
        if summary["state"] == storage.UNSEEN:
            if set(path) == set(expected_names):
                result["route"] = f"{name}_unobserved"
            return result
        if summary["state"] != storage.OBSERVED:
            return result
        sample = raw["sample"]
        frame = "established" if index in (0, 1) else "same_as_first_getter"
        if sample.get("storage_frame_relation") != frame:
            return result
        if index and (not sample.get("nested_inside_property_call_frame") or not sample.get("same_document_properties_owner")):
            return result
        if index == 0:
            if ((sample.get("property_owner_null"), sample.get("storage_argument_null"), sample.get("summary_owner_null"))
                    != (False, False, False) or sample.get("custom_data_argument") != 0 or sample.get("property_option_argument") != 0):
                return result
            summary.update({key: sample[key] for key in ("property_owner_null", "storage_argument_null", "summary_owner_null",
                                                        "custom_data_argument", "property_option_argument")})
        elif spec["sample"] != "signed_eax":
            if (sample.get("argument_owner_null") is not False or sample.get("matches_expected_owner") is not True
                    or sample.get("matches_expected_storage") is not True):
                return result
            summary.update({key: sample[key] for key in ("argument_owner_null", "matches_expected_owner", "matches_expected_storage")})
            if spec["sample"] == "property_set_mode":
                mode = sample.get("property_set_mode_u32")
                if (type(mode) is not int or not 0 <= mode < 1 << 32 or sample.get("property_set_mode_bytes") != 4
                        or type(sample.get("property_set_dom_null")) is not bool):
                    return result
                summary.update(property_set_mode_u32=mode, property_set_mode_bytes=4,
                               property_set_dom_null=sample["property_set_dom_null"])
        prior_end = raw["save_wait_ended_offset_ns"]
    if set(path) == set(expected_names):
        result["route"] = "all_property_stores_returned"
    return result

def observe_storage(*args, **kwargs):
    original = aggregate.engine.SaveAggregateTrace
    aggregate.engine.require(original is worker.BASE_TRACE, "unexpected prior debugger observer")
    aggregate.engine.SaveAggregateTrace = worker.PropertyBracketsTrace
    try:
        return aggregate.observe_aggregate(*args, **kwargs)
    finally:
        aggregate.engine.SaveAggregateTrace = original


def evaluate(report):
    lanes = report["lanes"]
    before, native, generated, after = (lanes.get(key) for key in ("ControlBefore", "ReducedNative", "Generated", "ControlAfter"))
    healthy = all(aggregate.native_control(row) for row in (before, native, after))
    native_trace, candidate_trace = storage_trace(native), storage_trace(generated)
    identities = states.process_identities(lanes.values())
    distinct = len(set(identities) - {None})
    paths = {(row["matched_input"], row["matched_save"]) for row in lanes.values()}
    reproduced = returns.generated_failure(generated)
    qualified = bool(healthy and distinct == len(identities) == 7 and len(paths) == 1 and reproduced
                     and native_trace["route"] == "all_property_stores_returned" and candidate_trace["route"] != storage.UNQUALIFIED
                     and report["inputs_immutable"] and report["last_debugger_cleanup_confirmed"]
                     and "exception" not in report and "control_after_exception" not in report)
    report.update(property_brackets_comparison_qualified=qualified, control_storage_trace=native_trace,
                  generated_storage_trace=candidate_trace, controls_healthy=healthy, distinct_processes=distinct,
                  same_physical_paths=len(paths) == 1, generated_failure_reproduced=reproduced,
                  generated_footprint=states.footprint(generated),
                  control_cleanup=((native or {}).get("save_aggregate_trace") or {}).get("breakpoint_cleanup"),
                  generated_cleanup=((generated or {}).get("save_aggregate_trace") or {}).get("breakpoint_cleanup"))


def run(packet, digest):
    job, source = read_packet(packet, digest)
    engine = aggregate.engine
    engine.require(os.name == "nt" and engine.pe_machine(Path(sys.executable).read_bytes()) == engine.AMD64,
                   "the fixed observer requires AMD64 Windows Python")
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / RESULTS
    output.mkdir(exist_ok=False)
    cleanup = {"confirmed": True}
    report = {"schema": SCHEMA, "packet_sha256": digest, "stops": job["stops"], "module_sha256": job["module_sha256"],
              "source_inside_call_receipt_sha256": SOURCE_RECEIPT_SHA256,
              "source_inside_call_host_sha256": SOURCE_HOST_SHA256,
              "observer_tool_sha256": job["tool_hashes"], "dbgeng_sdk_header_sha256": worker.SDK_HEADER_SHA256,
              "native_acceptance": False, "writer_output_count": 0, "heldout_inputs_tested": 0,
              "generated_attempted": False, "lanes": {}}
    pristine, native, _ = source["cases"]

    def measure(label, case, tree, *, debug=False):
        original_observer, original_events = events.observe_operation, events.EVENTS
        if debug:
            events.observe_operation = partial(observe_storage, engine_path=packet.parent / "Ancestor02" / "Engine" / "dbgeng.dll",
                                               oracle_hash=source["oracle_sha256"], identify=application_identity, cleanup=cleanup)
        else:
            events.observe_operation = partial(states.observe_operation, event7_return=0)
        events.EVENTS = original_events | frozenset(states.AUTOSAVE_HANDLERS)
        try:
            row = events.run_lane(Swapp, application_identity, packet=packet, row=case, oracle=source["oracle_sha256"],
                                  label=label, output=output, tree=tree)
        finally:
            events.observe_operation, events.EVENTS = original_observer, original_events
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
            control = measure("ReducedNative", native, tree, debug=True)
            if (cleanup["confirmed"] and aggregate.native_control(control)
                    and storage_trace(control)["route"] == "all_property_stores_returned"):
                report["generated_attempted"] = True
                measure("Generated", job["candidate"], job["candidate"]["expected_tree"], debug=True)
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
    parser = argparse.ArgumentParser(description="Observe the fixed general-property, summary and SolidWorks-property call/return boundaries")
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
    keys = ("property_brackets_comparison_qualified", "control_storage_trace", "generated_storage_trace", "control_cleanup",
            "generated_cleanup", "controls_healthy", "distinct_processes", "generated_failure_reproduced", "last_debugger_cleanup_confirmed")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["property_brackets_comparison_qualified"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
