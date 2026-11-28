from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

from AuditFilletArchive import (
    BUILD, CONFIG, CONTROL, DISCLOSED_LOCK, HERE, NAMES, ORACLE, RESOLVED, VERSION,
    SldprtArchive, audit_owners, checked, checked_json, guard_runtime, input_custody, require,
)
from AuditTypedFillet import BASELINE_PIN, BASELINE_REPORT
from FilletArchiveKernel import PARTITION
from FilletHistoryBody import check_shape_state
from ResolvedBridge import make_node
from Streams import StreamDoc

sys.path.insert(0, str(HERE.parent / "throughsource"))

from ReadTwoStockHistory import decode_history, ordered_frames, read_row, undo, verify_graph
from convert.Geometry.Parasolid import DecodePartData, ParaHeaderData
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Archive.Partition.SchemaHeader import SchemaHeader
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import CheckTreeAlias
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

CASE_SPEC = HERE / "DisclosedFilletInputs.json"
CASE_SPEC_PIN = "d985611e397e943860b8b0ce4b3f9631e6c31f5355bdd784519a2b028a9a51cb"
KERNEL_PIN = "2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969"
RECORD_PIN = "60f0c883e028c1689b8eb96a4cb75449a98f5f51"
ROLLBACK_READER_PIN = "42f7d6f1f1a9b77a134a46fa5230629879791cdef3ae4a1bd74a107a64a8f46f"
COUNTS = ("n_new_nodes", "n_del_nodes", "n_copy_mod_nodes")


def source_marks(link, features):
    marks = (RequireNative(link.ConfigValue.RootValue.FieldsValue["fe38"], "moPMarkRecord_c"),
             *(RequireNative(feature.FieldsValue["f3d0"], "moPMarkRecord_c") for feature in features))
    CheckTreeAlias(link, marks)
    require(all(set(mark.FieldsValue) == {"f18"} and type(mark.FieldsValue["f18"]) is int for mark in marks),
            "archive mark selector uses additional owner state")
    return tuple(mark.FieldsValue["f18"] for mark in marks)


def typed_fillet(archive, expected):
    headers = tuple(ReadHeaderGraph(archive.require(name), VERSION) for name in ("Header2", CONFIG + "-ModelHeader"))
    config = ReadConfigMut(archive.require(CONFIG), VERSION, headers[1], NodeMaker=make_node)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), VERSION)
    resolved = ReadResolvedMut(archive.require(RESOLVED), VERSION, config.MapValue, MakeLinkContext(config, manager),
                               ReadFillets=True, NodeMaker=make_node)
    link = NativeLink(config, resolved, CONFIG, RESOLVED)
    config_doc, resolved_doc = StreamDoc("config", {}, [config.RootValue]), StreamDoc(
        "resolved", {}, list(resolved.RootsValue))
    atom, owners = audit_owners(config_doc, resolved_doc, headers, expected["native_reopen"])
    require(owners == expected["owners"], "resolved fillet ownership changed before history verification")
    features = tuple(next(node for node in resolved.RootsValue if node.IndexValue == owners[key]["slot"])
                     for key in ("stock", "fillet"))
    return atom, owners, source_marks(link, features)


def expect_refusal(action, expected):
    try:
        action()
    except ValueError as error:
        require(str(error) == expected, f"unexpected history refusal: {error}")
        return str(error)
    raise ValueError("invalid history was admitted")


def frame_report(frame):
    refs = tuple(ref for row in (*frame.restored, *frame.changed) for ref in row.refs)
    return {
        "mark": frame.mark.IndexValue,
        "logical_id": frame.mark.Integer("id"),
        "earlier": frame.mark.Integer("preceding"),
        "later": frame.mark.Integer("first_following"),
        "delta_key": frame.mark.Integer("delta_key"),
        "rollback_payload_offset": frame.offset,
        "header_counts": {key: frame.mark.Integer(key) for key in COUNTS},
        "restored": dict(Counter(row.node.KindValue for row in frame.restored)),
        "removed": dict(Counter(kind for _, kind in frame.removed)),
        "previous_copies": dict(Counter(row.node.KindValue for row in frame.changed)),
        "copy_staging_capacity": frame.copy_capacity,
        "pointer_qualifiers": {
            "null_true": sum(not ref.index and ref.at_or_below_limit for ref in refs),
            "nonnull_true": sum(bool(ref.index and ref.at_or_below_limit) for ref in refs),
            "nonnull_false": sum(bool(ref.index and not ref.at_or_below_limit) for ref in refs),
        },
    }


def first_restored(payload, frame, preceding):
    header = ParaHeaderData(payload)
    offset = frame.offset - header.body_offset
    cursor = XmtCursor(payload[header.body_offset:])
    cursor.OffsetValue = offset
    kind = cursor.ReadKind()
    physical = read_row(cursor, kind)
    require(kind == 98 and physical == frame.restored[0] and not physical.refs
            and physical.node.IndexValue == preceding["label_value_slot"], "first restore has a foreign typed owner")
    return {
        "kind": kind, "class": KKernelShapes[kind].NameValue, "slot": physical.node.IndexValue,
        "record_interval": [offset, cursor.OffsetValue],
        "delta_payload_interval": [frame.offset, header.body_offset + cursor.OffsetValue],
        "first_use_descriptor_bytes": len(SchemaHeader(KKernelShapes[kind])),
        "wide_words": len(physical.node.Indexes("values")),
        "owner_attribute": "SWIMPLICITBODYNAME_ID_U",
        "owner_attribute_slot": preceding["label_attribute"], "owner_field": 0, "label": preceding["label"],
    }


def ordered_states(active, root, frames, ids):
    ordered = ordered_frames(root, frames, active, ids)
    reserved = {root.IndexValue, *frames}
    state = active
    world = verify_graph(active)
    defs = WalkXmtChain(active, world.Integer("attrib_def"), 80, PreviousField=None)
    global_nodes = {index: node for index, node in active.items() if node.KindValue in (79, 80)}
    require(set(defs) == {index for index, node in global_nodes.items() if node.KindValue == 80}
            and {active[index].Integer("identifier") for index in defs}
            == {index for index, node in global_nodes.items() if node.KindValue == 79},
            "physical WORLD does not own every global attribute definition")
    states = []
    for order, frame in enumerate(ordered):
        world = verify_graph(state)
        require(world.Integer("alive") == int(order < len(ordered) - 1)
                and all(state.get(index) == node for index, node in global_nodes.items())
                and (not order or not any(world.Integer(key) for key in ("attrib_def", "current_id", "highest_id"))),
                "rollback state does not retain actual global registry and WORLD ownership")
        if world.Integer("body"):
            (body,) = WalkXmtChain(state, world.Integer("body"), 12, OwnerField="owner", OwnerValue=1)
            require({body} == {node.IndexValue for node in state.values() if node.KindValue == 12},
                    "history includes a detached body")
        else:
            require(set(state) == {1, *global_nodes}, "body-free history retains unrelated geometry")
        states.append((world, state))
        if frame.mark.Integer("delta_key"):
            state = undo(state, frame, reserved)
    return ordered, tuple(states)


def events_match(ordered, states):
    (selected, stock, activation, initial) = ordered
    body = states[0][0].Integer("body")
    require(tuple(world.Integer("body") for world, _ in states) == (body, body, 0, 0) and body,
            "history is missing the retained body, stock and two empty states")
    changed = tuple({row.node.IndexValue for row in frame.changed} for frame in ordered)
    deleted_bodies = tuple({index for index, kind in frame.removed if kind == 12} for frame in ordered)
    require({1, body} <= changed[0] and changed[1:] == ({1}, {1}, set())
            and deleted_bodies == (set(), {body}, set(), set())
            and selected.restored and not any(row.node.KindValue == 12 for row in selected.restored)
            and not (stock.restored or activation.restored or activation.removed or initial.removed),
            "BODY restoration and deletion differ from the actual stock and fillet lifecycle")


def contrasts(current, root, frames, frame):
    reserved = {root.IndexValue, *frames}
    (index, kind), *remaining = frame.removed
    wrong = replace(frame, removed=((index, 14 if kind != 14 else 16), *remaining))
    crossed_slot = expect_refusal(lambda: undo(current, wrong, reserved),
                                  "rollback slots overlap or differ from their actual current class")
    target_counts = Counter(ref.index for row in (*frame.restored, *frame.changed) for ref in row.refs if ref.index)
    rows = list(frame.changed)
    row_position, ref_position = next((row_index, ref_index)
                                      for row_index, row in enumerate(rows)
                                      for ref_index, ref in enumerate(row.refs) if target_counts[ref.index] > 1)
    refs = list(rows[row_position].refs)
    refs[ref_position] = replace(refs[ref_position], at_or_below_limit=not refs[ref_position].at_or_below_limit)
    rows[row_position] = replace(rows[row_position], refs=tuple(refs))
    contradictory = replace(frame, changed=tuple(rows))
    changed_qualifier = expect_refusal(lambda: undo(current, contradictory, reserved),
                                       "inconsistent source-index selector for a rollback target")
    short = replace(frame, copy_capacity=len(frame.changed) - 1)
    copy_capacity = expect_refusal(lambda: undo(current, short, reserved),
                                    "rollback copy capacity or retained WORLD differs")
    return {"wrong_removal_class": crossed_slot, "contradictory_pointer_qualifier": changed_qualifier,
            "insufficient_copy_capacity": copy_capacity}


def fillet_history(raw, expected, case):
    archive = SldprtArchive.from_bytes(raw)
    atom, owners, ids = typed_fillet(archive, expected)
    active, history = DecodePartData(archive.require(PARTITION), PARTITION)
    nodes = ReadActiveNodes(active.data)
    refusal = expect_refusal(lambda: ReadXmtHistory(history.data, nodes), "current kernel framing differs")
    root, frames = decode_history(history.data)
    ordered, states = ordered_states(nodes, root, frames, ids)
    events_match(ordered, states)
    body = check_shape_state(states[0][1], states[1][1], expected, case, atom, owners)
    first = first_restored(history.data, ordered[0], body["prior_stock"])
    return {
        "source_sha256": expected["source_sha256"], "case": expected["case"], "edited": expected["edited"],
        "history_payload_sha256": history.sha256, "history_payload_bytes": len(history.data),
        "strict_delete_profile_refusal": refusal, "typed_history_consumes_payload": True,
        "root_slot": root.IndexValue,
        "selectors_from_typed_archive": list(ids), "physical_mark_order": [frame.mark.Integer("id") for frame in frames.values()],
        "chronological_rollback": [frame_report(frame) for frame in ordered],
        "state_node_counts": [len(nodes) for _, nodes in states], "first_restored": first, "body_integrity": body,
        "negative_contrasts": contrasts(nodes, root, frames, ordered[0]),
    }


def control_history(raw):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    revolve, = (node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moRevolution_c")
    ids = source_marks(link, (revolve,))
    active, history = DecodePartData(archive.require(PARTITION), PARTITION)
    nodes = ReadActiveNodes(active.data)
    _, previous = ReadHistMarks(history.data, nodes)
    root, frames = decode_history(history.data)
    ordered, states = ordered_states(nodes, root, frames, ids)
    require(previous == ids[0] and not any(frame.restored for frame in ordered)
            and ordered[0].copy_capacity == len(ordered[0].changed) == 1
            and any(index == states[0][0].Integer("body") and kind == 12 for index, kind in ordered[0].removed),
            "passing ordinary control differs from its selected-body deletion history")
    return {"source_sha256": CONTROL, "history_payload_sha256": history.sha256, "strict_prior_mark": previous,
            "selectors_from_typed_archive": list(ids), "chronological_rollback": [frame_report(frame) for frame in ordered],
            "state_node_counts": [len(state) for _, state in states], "typed_history_consumes_payload": True}


def worker(capture, control, case_name, edited):
    if not case_name:
        raw = checked(control, CONTROL)
        blocked = guard_runtime()
        result = control_history(raw)
    else:
        receipt = checked_json(BASELINE_REPORT, BASELINE_PIN)
        expected, = (row for row in receipt["results"] if row["case"] == case_name and row["edited"] == edited)
        shape, = (case for case in checked_json(CASE_SPEC, CASE_SPEC_PIN)["cases"] if case["name"] == case_name)
        name = case_name + ("Edited" if edited else "")
        raw = checked(capture / case_name / (name + ".SLDPRT"), expected["source_sha256"])
        blocked = guard_runtime()
        result = fillet_history(raw, expected, shape)
    require(not blocked, "history worker performed external access")
    return result | {"runtime_external_access_attempts": 0}


def launch(args, *option):
    command = (sys.executable, "-B", str(HERE / "AuditFilletHistory.py"), "--capture", str(args.capture),
               "--control", str(args.control), *option)
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    require(process.returncode == 0 and not process.stderr, f"guarded history worker failed: {process.stderr}")
    return json.loads(process.stdout)


def main():
    parser = ArgumentParser(description="Verify the disclosed SOLIDWORKS fillet rollback history")
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--report", type=Path)
    mode.add_argument("--worker", nargs=2, metavar=("CASE", "STATE"))
    mode.add_argument("--control-worker", action="store_true")
    args = parser.parse_args()
    if args.worker or args.control_worker:
        name, state = args.worker or (None, None)
        require(name is None or (name in NAMES and state in ("original", "edited")), "unsupported source request")
        print(json.dumps(worker(args.capture, args.control, name, state == "edited"), sort_keys=True, allow_nan=False))
        return 0
    require(not args.report.resolve().is_relative_to(args.capture.resolve()), "history receipt must stay outside capture")
    input_custody(args.capture)
    checked(HERE.parent / "throughsource" / "ReadTwoStockHistory.py", ROLLBACK_READER_PIN)
    results = [launch(args, "--worker", name, phase) for name in NAMES for phase in ("original", "edited")]
    control = launch(args, "--control-worker")
    report = {"schema": "kit.sw2026.edge-fillet-rollback-audit.v1", "oracle_build": BUILD, "oracle_sha256": ORACLE,
              "pskernel_sha256": KERNEL_PIN, "source_lock_sha256": DISCLOSED_LOCK, "codec_revision": RECORD_PIN,
              "disclosed_archive_receipt_sha256": BASELINE_PIN, "shared_rollback_reader_sha256": ROLLBACK_READER_PIN,
              "passed": True, "full_histories": len(results),
              "strict_control": control, "native_launches": 0, "private_cases_read": 0, "writer_outputs": 0,
              "production_history_admission": False, "results": results}
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"full_histories": len(results), "strict_control": True, "data_only": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
