from __future__ import annotations

import DrawingSaveAggregateDbgEng as engine
import InspectBlankDrawingSaveEventState as states
import InspectBlankDrawingSaveEvents as events


OBSERVER_FILES = ("DrawingSaveAggregateDbgEng.py", "InspectBlankDrawingSaveAggregate.py")
PACKAGE_SHA256 = "875678516f9ceed4a1c8b9b106d165106fcaa38723ad7c584c47b95b231600de"
STOP = {
    "module": "doccplu.dll",
    "module_sha256": engine.DOCCPLU_SHA256,
    "instruction_rva": engine.STOP_RVA,
    "stack_offset": engine.AGGREGATE_STACK_OFFSET,
    "bytes": engine.SAMPLE_BYTES,
}


def observe_aggregate(original, sw, controller, author, drawing, mode, expected, tree, source, target,
                      *, engine_path, oracle_hash, identify, cleanup):
    engine.require(mode == "RebuildSaveAs" and source.name == events.GENERATED_NAME
                   and target == source.parent / "open_and_save" / "SavedDrawing.SLDDRW",
                   "aggregate observer requires the owned matched SaveAs")
    identity = identify(controller.app)
    engine.require(identity["process_id"] == controller.process_id and controller.process_handle is not None
                   and sw.owned_process_ids() == {controller.process_id}
                   and identity["version_matches"] and identity["file_version"] == "34.5.2.0604"
                   and identity["sha256"] == oracle_hash and identity["pe_machine"] == hex(engine.AMD64),
                   "aggregate observer requires the pinned COM-owned process")

    trace = engine.SaveAggregateTrace(sw, engine_path, identity)
    event_trail = states.SaveEventStateTrail

    class AggregateEventTrail(event_trail):
        def OnFileSaveAsNotify(self, *args):
            returned = super().OnFileSaveAsNotify(*args)
            if self.start is not None and trace.save_entered.is_set() and not trace.save_returned.is_set():
                trace.result["event7_offset_ns"] = trace.event_offset()
                trace.event7_seen.set()
            return returned

    def save_once(*args):
        cleanup["confirmed"] = False
        trace.thread.start()
        try:
            engine.require(trace.ready.wait(engine.SETUP_SECONDS + 2), "debugger setup exceeded its deadline")
            engine.require(trace.result["armed"], trace.result.get("failure") or "software breakpoint could not be armed")
            return trace.call_owned_save(original, args)
        finally:
            result = trace.finish()
            cleanup["confirmed"] = result["cleanup_confirmed"]
            author.rec.data["save_aggregate_trace"] = result
            engine.require(cleanup["confirmed"], "debugger detach is unconfirmed for the owned COM process")

    states.SaveEventStateTrail = AggregateEventTrail
    try:
        return states.observe_operation(save_once, sw, controller, author, drawing, mode, expected, tree, source, target,
                                        event7_return=0)
    finally:
        states.SaveEventStateTrail = event_trail


def native_control(row):
    return bool(row and row["passed"] and states.observed_sequence(row) == states.CONTROL_EVENTS)


def qualified_sample(row):
    trace = row.get("save_aggregate_trace") if row else None
    if not trace or not trace["armed"] or trace["failure"] is not None or not trace["cleanup_confirmed"] or not trace.get("breakpoint_removed"):
        return None
    sample = trace["sample"]
    if sample is None:
        return None
    if (sample["rva"], sample["effective_processor"], sample["executing_processor"], sample["bytes_read"], sample["event7_seen"]) != (
        engine.STOP_RVA, hex(engine.AMD64), hex(engine.AMD64), engine.SAMPLE_BYTES, True,
    ):
        return None
    return sample["aggregate"]
