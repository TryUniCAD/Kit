from __future__ import annotations

import argparse
import json
from pathlib import Path
from shutil import copyfile
from time import monotonic_ns

import AuthorCurves as curves
import InspectDrawingSaveModes as modes
from InspectBlankDrawingPair import GENERATED_NAME, TOOL_NAMES as PAIR_TOOLS
from InspectDrawingCache import phase


SCHEMA = "kit.sw2026.blank-drawing-save-event-trial.v1"
CASES = ("Pristine", "ReducedNative", "Generated")
TOOLS = (*PAIR_TOOLS, "InspectDrawingSaveModes.py", "InspectBlankDrawingSaveEvents.py")
EARLY_EVENTS = frozenset((6, 7))
STORAGE_EVENTS = frozenset((9, 28))
EVENTS = EARLY_EVENTS | STORAGE_EVENTS


class EventTrail:
    def __init__(self):
        self.start = None
        self.timeline = []

    def append(self, ordinal):
        if self.start is not None:
            self.timeline.append([ordinal, monotonic_ns() - self.start])
        return 0

    def OnFileSaveNotify(self, *_):
        return self.append(6)

    def OnFileSaveAsNotify(self, *_):
        return self.append(7)

    def OnSaveToStorageNotify(self, *_):
        return self.append(9)

    def OnSaveToStorageStoreNotify(self, *_):
        return self.append(28)


def bind_event_trail(author, drawing):
    source = author.interfaces.DrawingDoc.default_source
    expected = "{83A33D34-37C5-11CE-BFD4-00400513BB57}"
    curves.require(str(source.CLSID_Sink).upper() == expected, "drawing event source differs from the pinned type library")

    class DrawingSaveEvents(EventTrail, source):
        def __init__(self, native):
            EventTrail.__init__(self)
            source.__init__(self, native)

    return DrawingSaveEvents(drawing)


def observe_operation(original, sw, controller, author, drawing, mode, expected, tree, source, target):
    sink = bind_event_trail(author, drawing)
    sink.start = monotonic_ns()
    try:
        return original(sw, controller, author, drawing, mode, expected, tree, source, target)
    finally:
        elapsed = monotonic_ns() - sink.start
        try:
            sw.pythoncom.PumpWaitingMessages()
        finally:
            author.rec.data["save_event_trace"] = {"save_return_ns": elapsed, "events": list(sink.timeline)}
            sink.close()


def input_path(root, row):
    return root / "Inputs" / row["name"] / GENERATED_NAME


def read_packet(path, expected_hash):
    curves.require(curves.digest(path) == expected_hash, "drawing save event packet changed")
    request = json.loads(path.read_bytes())
    rows = request["cases"]
    curves.require(request["schema"] == SCHEMA and request["native_acceptance"] is False
                   and request["writer_output_count"] == 0 and request["heldout_inputs_tested"] == 0,
                   "expected an existing drawing input observer")
    curves.require(tuple(row["name"] for row in rows) == CASES and rows[0]["sha256"] == request["control_sha256"],
                   "unexpected drawing save event source list")
    curves.require(set(request["tool_hashes"]) == set(TOOLS), "unexpected drawing save event tool list")
    for name in TOOLS:
        curves.require(curves.digest(Path(__file__).with_name(name)) == request["tool_hashes"][name], f"observer tool changed: {name}")
    for row in rows:
        artifact = input_path(path.parent, row)
        curves.require(artifact.stat().st_size == row["bytes"] and curves.digest(artifact) == row["sha256"], "drawing save event input changed")
        curves.require(row["expected"]["view"] is None, "drawing save event observer requires blank sheets")
    return request


def run_lane(sw, identify, *, packet, row, oracle, label, output, tree):
    work = output / "MatchedDrawing"
    work.mkdir(exist_ok=False)
    source = work / GENERATED_NAME
    copyfile(input_path(packet.parent, row), source)
    original = modes.save_rebuilt

    def observed(*args):
        return observe_operation(original, *args)

    modes.save_rebuilt = observed
    try:
        first = modes.save_phase(sw, identify, row=row, mode="RebuildSaveAs", working=work, source=source,
                                 oracle=oracle, expected_tree=tree)
    finally:
        modes.save_rebuilt = original
    record = json.loads((work / "open_and_save" / "Record.json").read_bytes())
    trace = record.get("save_event_trace")
    if trace is not None:
        ordered = trace["events"]
        curves.require(all(ordinal in EVENTS and offset >= 0 for ordinal, offset in ordered)
                       and [event[1] for event in ordered] == sorted(event[1] for event in ordered),
                       "drawing save event trace is malformed")
    target = work / first["save_target_relative_path"]
    reopened = None
    if first["passed"]:
        reopened = phase(sw, identify, directory=work / "fresh_reopen", native=target,
                         expected_hash=first["save_target_sha256"], expected=first["expected_reopen"],
                         tree=first["tree"], oracle_sha=oracle, edit=False)
    evidence = {"name": label, "input_sha256": row["sha256"], "save_event_trace": trace,
                "matched_input": source.relative_to(output).as_posix(), "matched_save": target.relative_to(output).as_posix(),
                "open_and_save": first, "fresh_reopen": reopened, "passed": bool(first["passed"] and reopened and reopened["passed"])}
    work.rename(output / label)
    return evidence


def event_ordinals(row):
    trace = row.get("save_event_trace")
    return frozenset(ordinal for ordinal, offset in trace["events"] if offset <= trace["save_return_ns"]) if trace is not None else frozenset()


def evaluate(report):
    lanes = report["lanes"]
    names = ("ControlBefore", "ReducedNative", "Generated", "ControlAfter")
    phases = [item for row in lanes.values() for key in ("open_and_save", "fresh_reopen") if (item := row[key]) is not None]
    processes = {item["oracle_identity"]["process_creation_filetime"] for item in phases if "oracle_identity" in item}
    paths = {(row["matched_input"], row["matched_save"]) for row in lanes.values()}
    control_keys = ("ControlBefore", "ReducedNative", "ControlAfter")
    controls = [lanes.get(name) for name in control_keys]
    healthy = all(row is not None and row["passed"] for row in controls)
    sink_proven = bool(healthy and all(event_ordinals(row) & STORAGE_EVENTS for row in controls))
    early_proven = bool(healthy and all(event_ordinals(row) & EARLY_EVENTS for row in controls))
    generated = lanes.get("Generated")
    reproduced = bool(generated and tuple(generated["open_and_save"].get("save_status") or ()) == (False, 1, 0)
                      and generated["open_and_save"].get("save_target_bytes") == 0 and not generated["passed"])
    trace_present = generated is not None and generated["save_event_trace"] is not None
    interpretable = bool(set(lanes) == set(names) and len(paths) == 1 and len(processes) == len(phases)
                         and "exception" not in report and sink_proven and reproduced and trace_present)
    edge = None
    if interpretable:
        marks = event_ordinals(generated)
        if marks & STORAGE_EVENTS:
            edge = "after_third_party_storage_notification"
        elif marks & EARLY_EVENTS:
            edge = "after_storage_dispatch_before_third_party_storage_notification"
        elif early_proven:
            edge = "before_observed_storage_dispatch_notification"
        else:
            edge = "before_observed_third_party_storage_notification"
    report.update(distinct_processes=len(processes), same_physical_paths=len(paths) == 1,
                  controls_healthy=healthy, storage_event_controls_passed=sink_proven, early_event_controls_passed=early_proven,
                  original_failure_reproduced=reproduced, interpretable=interpretable, observed_save_edge=edge)


def run(packet, expected_hash):
    job = read_packet(packet, expected_hash)
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / "DrawingSaveEventResults"
    output.mkdir(exist_ok=False)
    report = {"schema": "kit.sw2026.blank-drawing-save-event-result.v1", "packet_sha256": expected_hash,
              "writer_output_count": 0, "native_acceptance": False, "heldout_inputs_tested": 0, "lanes": {}}
    pristine, reduced, generated = job["cases"]

    def measure(label, row, tree):
        result = run_lane(Swapp, application_identity, packet=packet, row=row, oracle=job["oracle_sha256"],
                          label=label, output=output, tree=tree)
        report["lanes"][label] = result
        curves.write_json(output / "Progress.json", report)
        return result

    tree = None
    try:
        before = measure("ControlBefore", pristine, None)
        if before["passed"] and event_ordinals(before) & STORAGE_EVENTS:
            tree = before["open_and_save"]["tree"]
            native = measure("ReducedNative", reduced, tree)
            if native["passed"] and event_ordinals(native) & STORAGE_EVENTS:
                measure("Generated", generated, generated["expected_tree"])
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        abandoned = output / "MatchedDrawing"
        try:
            if abandoned.exists():
                abandoned.rename(output / "InterruptedLane")
            measure("ControlAfter", pristine, tree)
        except Exception as error:
            report["control_after_exception"] = repr(error)
    read_packet(packet, expected_hash)
    report["inputs_immutable"] = True
    evaluate(report)
    curves.write_json(output / "DrawingBlankSaveEventsResults.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Observe passive drawing COM save notifications on matched private copies")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    packet = arguments.packet.resolve()
    if arguments.verify_only:
        read_packet(packet, arguments.packet_sha256)
        return 0
    result = run(packet, arguments.packet_sha256)
    print(json.dumps({key: result[key] for key in ("interpretable", "observed_save_edge", "distinct_processes")}))
    return 0 if result["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
