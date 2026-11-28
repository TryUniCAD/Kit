from __future__ import annotations

import argparse
from functools import partial
import json
import os
from pathlib import Path
import sys

import DrawingSavePropertyStorageModeDbgEng as worker
import InspectBlankDrawingSaveAggregateSoftwarePropertiesEntryMatched as previous
import InspectBlankDrawingSaveAggregate as aggregate
import InspectBlankDrawingSaveAggregateSoftwareStorageMatched as storage
import InspectBlankDrawingSaveEventState as states
import InspectBlankDrawingSaveEvents as events


SCHEMA = "kit.sw2026.blank-drawing-property-storage-mode-matched.v1"
RESULTS = "DrawingSavePropertyStorageModeMatchedResults"
RECEIPT = "DrawingBlankSavePropertyStorageModeMatchedResults.json"
SOURCE_PACKET_SHA256 = "5f4351c61f933694b75a0d55f969172e49cb991a674a87e810868040375a1cfd"
SOURCE_ENTRY_RECEIPT_SHA256 = "8124657abeac2870d48f221a9b408c38e132349ee4a73c9afa2d179891a5c3b2"
SOURCE_ENTRY_HOST_SHA256 = "0677731e0078afb29565798d27b8187b9e5aced03d8bee263c3a1c763068fdd8"
SOURCE_SECTIONS_RECEIPT_SHA256 = "3e812322931dbaf696dfb56fc25ca23d22be3e75290bb4b2f30223159b96e784"
SOURCE_SECTIONS_HOST_SHA256 = "d37226b31d7b976bc04117886fe566f16bb6a9634fc1f02c1c869bb97eea96df"
CANDIDATE_SHA256 = "7400cf1fa4a71994807ce8e49283e2721e09a5ceaf723e36f6ae807906c94a26"


def read_packet(packet, digest):
    require = aggregate.engine.require
    require(events.curves.digest(packet) == digest, "storage-mode packet differs from its pinned hash")
    job = json.loads(packet.read_bytes())
    require(job["schema"] == SCHEMA and job["source_properties_entry_packet_sha256"] == SOURCE_PACKET_SHA256
            and job["source_properties_entry_receipt_sha256"] == SOURCE_ENTRY_RECEIPT_SHA256
            and job["source_properties_entry_host_sha256"] == SOURCE_ENTRY_HOST_SHA256
            and job["source_sections_receipt_sha256"] == SOURCE_SECTIONS_RECEIPT_SHA256
            and job["source_sections_host_sha256"] == SOURCE_SECTIONS_HOST_SHA256
            and job["stops"] == list(worker.STOPS) and job["module_sha256"] == worker.MODULE_SHA256
            and job["dbgeng_sdk_header_sha256"] == worker.SDK_HEADER_SHA256
            and job["native_acceptance"] is False and job["heldout_inputs_tested"] == 0
            and job["writer_output_count"] == 0, "unexpected fixed storage-mode packet")
    tools = Path(__file__).parent
    require(set(job["tool_hashes"]) == {path.name for path in tools.glob("*.py")}, "unexpected storage-mode tool list")
    for name, expected in job["tool_hashes"].items():
        require(events.curves.digest(tools / name) == expected, f"{name} differs from the packet")
    for name, expected in job["custody_files"].items():
        require(Path(name).name == name and events.curves.digest(packet.parent / name) == expected,
                "frozen custody file differs")
    _, _, _, _, source = previous.read_packet(packet.with_name("SourcePropertiesEntryTrial.json"), SOURCE_PACKET_SHA256)
    candidate = job["candidate"]
    artifact = events.input_path(packet.parent, candidate)
    require(candidate["name"] == "GeneratedSections" and candidate["sha256"] == CANDIDATE_SHA256
            and artifact.stat().st_size == candidate["bytes"] and events.curves.digest(artifact) == CANDIDATE_SHA256
            and candidate["expected"] == source["cases"][2]["expected"]
            and candidate["expected_tree"] == source["cases"][2]["expected_tree"], "corrected candidate differs")
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
    path = trace.get("property_storage_path") or {}
    result = {"route": storage.UNQUALIFIED, "stages": {}}
    if not qualified_aggregate(row):
        return result
    prior_end = trace.get("save_wait_ended_offset_ns")
    expected_names = []

    def stage(name, rva, *, eax=False):
        nonlocal prior_end
        expected_names.append(name)
        raw = path.get(name) or {}
        summary = storage.stage_summary(trace, raw, expected_rva=rva, previous_stop_end=prior_end, require_eax=eax)
        result["stages"][name] = summary
        expected_frame = "established" if len(expected_names) == 1 else "same_as_first_getter"
        if raw.get("module") != "sldappu.dll":
            summary["state"] = storage.UNQUALIFIED
        if summary["state"] == storage.OBSERVED and raw["sample"].get("storage_frame_relation") != expected_frame:
            summary["state"] = storage.UNQUALIFIED
        if summary["state"] == storage.UNSEEN and set(path) == set(expected_names):
            result["route"] = f"{name}_unobserved"
        if summary["state"] == storage.OBSERVED:
            prior_end = raw["save_wait_ended_offset_ns"]
        return summary, raw.get("sample") or {}

    mode, mode_sample = stage("storage_mode", worker.STORAGE_MODE_RVA, eax=True)
    if mode["state"] != storage.OBSERVED:
        return result
    if type(mode_sample.get("retained_istorage_null")) is not bool or type(mode_sample.get("storage_wrapper_null")) is not bool:
        return result
    mode.update(retained_istorage_null=mode_sample["retained_istorage_null"], storage_wrapper_null=mode_sample["storage_wrapper_null"])
    if mode["eax_signed"] == 0 and mode_sample["retained_istorage_null"]:
        fallback, _ = stage("fallback_storage_hresult", worker.FALLBACK_HRESULT_RVA, eax=True)
        if fallback["state"] != storage.OBSERVED:
            return result
        if fallback["eax_signed"] < 0:
            if set(path) == set(expected_names):
                result["route"] = "fallback_storage_negative_hresult_observed"
            return result
    call, arguments = stage("property_store_call", worker.PROPERTY_CALL_RVA)
    if call["state"] != storage.OBSERVED:
        return result
    if (type(arguments.get("property_owner_null")) is not bool or type(arguments.get("storage_argument_null")) is not bool
            or arguments.get("custom_data_argument") != 0 or arguments.get("property_option_argument") != 0
            or (arguments["property_owner_null"] and arguments.get("summary_owner_null") is not None)
            or (not arguments["property_owner_null"] and type(arguments.get("summary_owner_null")) is not bool)):
        return result
    call.update({key: arguments[key] for key in ("property_owner_null", "storage_argument_null", "summary_owner_null",
                                               "custom_data_argument", "property_option_argument")})
    returned, _ = stage("property_store_return", worker.PROPERTY_RETURN_RVA, eax=True)
    if returned["state"] == storage.OBSERVED and set(path) == set(expected_names):
        result["route"] = "property_store_return_observed"
    elif returned["state"] == storage.UNSEEN and set(path) == set(expected_names):
        result["route"] = "property_store_return_unobserved"
    return result


def observe_storage(*args, **kwargs):
    original = aggregate.engine.SaveAggregateTrace
    aggregate.engine.require(original is worker.BASE_TRACE, "unexpected prior debugger observer")
    aggregate.engine.SaveAggregateTrace = worker.PropertyStorageModeTrace
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
    reproduced = previous.preview.returns.generated_failure(generated)
    qualified = bool(healthy and distinct == len(identities) == 7 and len(paths) == 1 and reproduced
                     and native_trace["route"] == "property_store_return_observed" and candidate_trace["route"] != storage.UNQUALIFIED
                     and report["inputs_immutable"] and report["last_debugger_cleanup_confirmed"]
                     and "exception" not in report and "control_after_exception" not in report)
    report.update(storage_mode_comparison_qualified=qualified, control_storage_trace=native_trace,
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
              "source_properties_entry_receipt_sha256": SOURCE_ENTRY_RECEIPT_SHA256,
              "source_sections_receipt_sha256": SOURCE_SECTIONS_RECEIPT_SHA256,
              "observer_tool_sha256": job["tool_hashes"], "dbgeng_sdk_header_sha256": worker.SDK_HEADER_SHA256,
              "native_acceptance": False, "writer_output_count": 0, "heldout_inputs_tested": 0,
              "generated_attempted": False, "lanes": {}}
    pristine, native, _ = source["cases"]

    def measure(label, case, tree, *, debug=False):
        original_observer, original_events = events.observe_operation, events.EVENTS
        if debug:
            events.observe_operation = partial(observe_storage, engine_path=packet.parent / "Engine" / "dbgeng.dll",
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
                    and storage_trace(control)["route"] == "property_store_return_observed"):
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
    parser = argparse.ArgumentParser(description="Observe the fixed property-storage selection and inner writer boundary")
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
    keys = ("storage_mode_comparison_qualified", "control_storage_trace", "generated_storage_trace", "control_cleanup",
            "generated_cleanup", "controls_healthy", "distinct_processes", "generated_failure_reproduced", "last_debugger_cleanup_confirmed")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["storage_mode_comparison_qualified"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
