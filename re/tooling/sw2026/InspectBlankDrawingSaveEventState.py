from __future__ import annotations

import argparse
import json
from functools import partial
from pathlib import Path
from time import monotonic_ns

import InspectBlankDrawingSaveEvents as events

SCHEMA = "kit.sw2026.blank-drawing-save-event-state.v1"
SOURCE_IID = "{83A33D34-37C5-11CE-BFD4-00400513BB57}"
AUTOSAVE_HANDLERS = {
    11: "OnAutoSaveToStorageNotify",
    48: "OnAutoSaveToStorageStoreNotify",
}
CONTROL_EVENTS = (7, 9, 28)
PASSIVE_LANES = ("ControlBefore", "ReducedNative", "Generated", "ControlAfter")
CALIBRATION = {"name": "VetoCalibration", "input_case": "ReducedNative", "event": 7, "return_value": 1}
RESULTS = "DrawingSaveEventStateResults"


def snapshot(target):
    try:
        return {"exists": True, "bytes": target.stat().st_size}
    except FileNotFoundError:
        return {"exists": False, "bytes": None}
    except OSError as error:
        return {"exists": None, "bytes": None, "errno": error.errno, "winerror": getattr(error, "winerror", None)}


class SaveEventStateTrail(events.EventTrail):
    def __init__(self, target, event7_return):
        super().__init__()
        self.target = target
        self.event7_return = event7_return
        self.event7_states = []

    def OnFileSaveAsNotify(self, *_):
        if self.start is None:
            return 0
        self.append(7)
        self.event7_states.append({
            "offset_ns": self.timeline[-1][1],
            "target_state": snapshot(self.target),
            "return_value": self.event7_return,
        })
        return self.event7_return

    def OnAutoSaveToStorageNotify(self, *_):
        return self.append(11)

    def OnAutoSaveToStorageStoreNotify(self, *_):
        return self.append(48)


def observe_operation(original, sw, controller, author, drawing, mode, expected, tree, source, target,
                      *, event7_return):
    interface = author.interfaces.DrawingDoc.default_source
    events.curves.require(str(interface.CLSID_Sink).upper() == SOURCE_IID, "drawing event source differs from the pinned type library")
    dispatch = getattr(interface, "_dispid_to_func_", {}) or {}
    advertised_autosave = [ordinal for ordinal, name in AUTOSAVE_HANDLERS.items() if dispatch.get(ordinal) == name]

    class DrawingSaveEventState(SaveEventStateTrail, interface):
        def __init__(self, native):
            SaveEventStateTrail.__init__(self, target, event7_return)
            interface.__init__(self, native)

    sink = DrawingSaveEventState(drawing)
    try:
        visible_path = str(author.get(author.model, "GetPathName"))
        save_flag = bool(author.get(author.model, "GetSaveFlag"))
        before = snapshot(target)
        sink.start = monotonic_ns()
        try:
            return original(sw, controller, author, drawing, mode, expected, tree, source, target)
        finally:
            elapsed = monotonic_ns() - sink.start
            after = snapshot(target)
            try:
                sw.pythoncom.PumpWaitingMessages()
            finally:
                author.rec.data["save_event_trace"] = {
                    "save_return_ns": elapsed,
                    "events": list(sink.timeline),
                    "advertised_autosave_ordinals": advertised_autosave,
                    "visible_path_before_save": visible_path,
                    "save_flag_before_save": save_flag,
                    "target_before_save": before,
                    "event7_states": list(sink.event7_states),
                    "target_after_save_return": after,
                }
    finally:
        sink.close()


def read_packet(packet, expected_hash):
    job = events.read_packet(packet, expected_hash)
    observer = job["state_observer"]
    events.curves.require(observer["schema"] == SCHEMA and observer["filename"] == Path(__file__).name
                          and observer["sha256"] == events.curves.digest(Path(__file__))
                          and observer["calibration"] == CALIBRATION,
                          "unexpected drawing save state observer")
    return job


def observed_sequence(row):
    trace = row.get("save_event_trace") if row else None
    if trace is None:
        return ()
    return tuple(ordinal for ordinal, offset in trace["events"] if offset <= trace["save_return_ns"])


def synchronous_event7(trace):
    return [item for item in trace["event7_states"] if item["offset_ns"] <= trace["save_return_ns"]]


def footprint(row):
    if not row or row["save_event_trace"] is None or "save_status" not in row["open_and_save"]:
        return None
    trace = row["save_event_trace"]
    event7 = [item["target_state"] for item in synchronous_event7(trace)]
    states = (trace["target_before_save"], *event7, trace["target_after_save_return"])
    if any(state["exists"] is None for state in states):
        return None
    return {
        "event_ordinals": list(observed_sequence(row)),
        "save_status": list(row["open_and_save"]["save_status"]),
        "target_states": list(states),
    }


def process_identities(lanes):
    return [phase.get("oracle_identity", {}).get("process_creation_filetime")
            for lane in lanes for key in ("open_and_save", "fresh_reopen")
            if (phase := lane[key]) is not None]


def evaluate(report):
    events.evaluate(report)
    lanes = report["lanes"]
    controls = (lanes.get("ControlBefore"), lanes.get("ReducedNative"), lanes.get("ControlAfter"))
    controls_match = all(observed_sequence(row) == CONTROL_EVENTS for row in controls)
    generated = lanes.get("Generated")
    passive_processes = process_identities(lanes.values())
    passive_fresh = None not in passive_processes and len(set(passive_processes)) == len(passive_processes)
    passive_complete = set(lanes) == set(PASSIVE_LANES) and all(
        row["save_event_trace"] is not None and "save_status" in row["open_and_save"]
        and all(item["return_value"] == 0 for item in synchronous_event7(row["save_event_trace"]))
        for row in lanes.values()
    )
    passive_interpretable = bool(passive_complete and passive_fresh and controls_match and report["controls_healthy"]
                                 and report["same_physical_paths"] and "exception" not in report
                                 and "control_after_exception" not in report)
    sequence = observed_sequence(generated)
    calibration = report.get("veto_calibration")
    calibration_footprint = footprint(calibration)
    generated_footprint = footprint(generated)
    observed_processes = passive_processes + (process_identities((calibration,)) if calibration else [])
    calibration_interpretable = False
    if passive_interpretable and calibration and calibration["save_event_trace"] is not None:
        first = calibration["open_and_save"]
        trace = calibration["save_event_trace"]
        status = first.get("save_status")
        returns = [item["return_value"] for item in synchronous_event7(trace)]
        calibration_interpretable = (
            status and status[0] is False and first["open_errors"] == first["open_warnings"] == 0
            and first["initial"] and first["rebuilt"] and not first["dialogs"] and not first["controller_diagnostics"]
            and observed_sequence(calibration) == (7,) and returns == [1]
            and calibration["matched_input"] == generated["matched_input"]
            and calibration["matched_save"] == generated["matched_save"]
            and None not in observed_processes and len(set(observed_processes)) == len(observed_processes)
        )
    footprints_comparable = calibration_interpretable and generated_footprint is not None and calibration_footprint is not None
    report.update(
        interpretable=passive_interpretable,
        passive_control_sequences_match=controls_match,
        generated_ordinals=list(sequence),
        generated_ordinary_storage_callback_seen=bool(set(sequence) & events.STORAGE_EVENTS),
        generated_autosave_callback_seen=bool(set(sequence) & AUTOSAVE_HANDLERS.keys()),
        generated_footprint=generated_footprint,
        veto_footprint=calibration_footprint,
        veto_calibration_interpretable=bool(calibration_interpretable),
        veto_footprint_matches_generated=(calibration_footprint == generated_footprint) if footprints_comparable else None,
        total_distinct_processes=len(set(observed_processes) - {None}),
    )
    report.pop("observed_save_edge", None)


def run(packet, expected_hash):
    job = read_packet(packet, expected_hash)
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / RESULTS
    output.mkdir(exist_ok=False)
    report = {
        "schema": SCHEMA,
        "packet_sha256": expected_hash,
        "state_observer_sha256": job["state_observer"]["sha256"],
        "source_event_packet_sha256": job["state_observer"]["source_event_packet_sha256"],
        "writer_output_count": 0,
        "native_acceptance": False,
        "heldout_inputs_tested": 0,
        "lanes": {},
        "veto_calibration": None,
    }
    pristine, reduced, generated = job["cases"]

    def measure(label, row, tree, *, event7_return=0):
        original_observer, original_events = events.observe_operation, events.EVENTS
        events.observe_operation = partial(observe_operation, event7_return=event7_return)
        events.EVENTS = original_events | frozenset(AUTOSAVE_HANDLERS)
        try:
            result = events.run_lane(Swapp, application_identity, packet=packet, row=row, oracle=job["oracle_sha256"],
                                     label=label, output=output, tree=tree)
        finally:
            events.observe_operation, events.EVENTS = original_observer, original_events
        if event7_return:
            report["veto_calibration"] = result
        else:
            report["lanes"][label] = result
        events.curves.write_json(output / "Progress.json", report)
        return result

    tree = None
    try:
        before = measure("ControlBefore", pristine, None)
        if before["passed"] and observed_sequence(before) == CONTROL_EVENTS:
            tree = before["open_and_save"]["tree"]
            native = measure("ReducedNative", reduced, tree)
            if native["passed"] and observed_sequence(native) == CONTROL_EVENTS:
                measure("Generated", generated, generated["expected_tree"])
                try:
                    measure(CALIBRATION["name"], reduced, tree, event7_return=CALIBRATION["return_value"])
                except Exception as error:
                    report["veto_calibration_exception"] = repr(error)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            interrupted = output / "MatchedDrawing"
            if interrupted.exists():
                interrupted.rename(output / "InterruptedLane")
            measure("ControlAfter", pristine, tree)
        except Exception as error:
            report["control_after_exception"] = repr(error)
    read_packet(packet, expected_hash)
    report["inputs_immutable"] = True
    evaluate(report)
    events.curves.write_json(output / "DrawingBlankSaveEventStateResults.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Observe target file metadata and pinned drawing COM save callbacks")
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
    keys = ("interpretable", "original_failure_reproduced", "generated_ordinals",
            "veto_calibration_interpretable", "veto_footprint_matches_generated", "total_distinct_processes")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
