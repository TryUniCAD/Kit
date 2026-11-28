from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
from struct import pack
import subprocess
import sys

from AuditFilletHistory import (
    BUILD, CONTROL, DISCLOSED_LOCK, HERE, NAMES, ORACLE, PARTITION, ReadActiveNodes,
    SldprtArchive, checked, checked_json, control_history, decode_history, DecodePartData,
    expect_refusal, guard_runtime, input_custody, ordered_states, ParaHeaderData, require,
    XmtCursor,
)
from AuditFilletArchive import ROOT
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtStages import ReadXmtStages
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import ReadXmtValueMut
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletHist import ReadFilletHist
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletOwn import ReadFilletOwn
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

BASELINE_REVISION = "872478d2b7026941949d98036465bb615854c5e1"
BASELINE_PIN = "a8b954ac2eab2d5064055282cf1f029bec4d0a2ba83c4b09e1023d646f06b849"
BASELINE = ROOT / "re/solidworks/measurements/2026/EdgeFilletRollbackRead01.json"


def source(capture, row):
    name = row["case"]
    stem = name + ("Edited" if row["edited"] else "")
    return checked(capture / name / (stem + ".SLDPRT"), row["source_sha256"])


def compare_stages(result, reference, states):
    require(len(result.StagesValue) == len(reference) == len(states) == 4,
            "production stage inventory differs")
    for stage, archived, (_, state) in zip(result.StagesValue, reference, states, strict=True):
        require(stage.MarkValue == archived.mark and stage.NodesValue == state,
                "complete production state differs from the independent historical graph")
        delta = stage.UndoValue
        if archived.mark.Integer("delta_key"):
            flags = {ref.index: ref.at_or_below_limit
                     for row in (*archived.restored, *archived.changed) for ref in row.refs}
            require(delta is not None and delta.Qualifiers == flags
                    and delta.CopyCapacity == archived.copy_capacity and delta.RemovedValue == archived.removed
                    and delta.RestoredValue == tuple(row.node for row in archived.restored)
                    and delta.PreviousValue == tuple(row.node for row in archived.changed),
                    "complete typed transaction differs from its independent physical field owners")
        else:
            require(delta is None, "production initial state has a foreign transaction")


def qualified_offsets(payload, frame):
    header = ParaHeaderData(payload)
    packet = XmtCursor(payload[header.body_offset:])
    packet.OffsetValue = frame.offset - header.body_offset
    packet.SeenKinds.update((3, 4))
    pointers = []

    def read_value(cursor, field, previous):
        if field.EncodingValue != "p":
            return ReadXmtValueMut(cursor, field, previous)
        start = header.body_offset + cursor.OffsetValue
        target = cursor.ReadIndex()
        flag_offset = header.body_offset + cursor.OffsetValue
        flag, = cursor.TakeBytes(1)
        pointers.append((start, flag_offset, target, flag))
        return target

    def rows():
        values = []
        while (kind := packet.ReadKind()) != 1:
            values.append(ReadXmtNodeMut(packet, kind, ValueReader=read_value))
        require(packet.ReadIndex() == 0, "record offset witness stopped before the real terminator")
        return tuple(values)

    require(rows() == tuple(row.node for row in frame.restored), "restored-row offset witness differs")
    removals = []
    while index := packet.ReadIndex():
        offset = header.body_offset + packet.OffsetValue
        removals.append((index, packet.ReadKind(), offset))
    capacity = header.body_offset + packet.OffsetValue
    require(packet.TakeBytes(4) == pack(">i", frame.copy_capacity)
            and tuple((index, kind) for index, kind, _ in removals) == frame.removed
            and rows() == tuple(row.node for row in frame.changed), "previous-row offset witness differs")
    return removals[0], capacity, pointers


def replace_span(payload, offset, data):
    return payload[:offset] + data + payload[offset + len(data):]


def wire_refusals(payload, nodes, ids, ordered, states):
    frame = ordered[0]
    (_, kind, kind_offset), capacity_offset, pointers = qualified_offsets(payload, frame)
    flag_counts = Counter(target for _, _, target, _ in pointers if target)
    pointer, flag_pos, target, flag = next(row for row in pointers
                                          if row[1] - row[0] == 2 and flag_counts[row[2]] > 1)
    foreign = max(max(state) for _, state in states) + 1
    bad_kind, bad_capacity = 14 if kind != 14 else 16, len(frame.changed) - 1
    variants = {
        "foreign_removal_class": (kind_offset, pack(">H", bad_kind),
                                  "rollback slots overlap or disagree with the actual live owners"),
        "short_copy_capacity": (capacity_offset, pack(">i", bad_capacity),
                                "rollback rows exceed their bounded capacity"),
        "contradictory_source_qualifier": (flag_pos, bytes((1 - flag,)),
                                          "inconsistent source index selector for a rollback target"),
        "unresolved_previous_dependency": (pointer, pack(">h", foreign + 1),
                                           "rollback graph has an unresolved pointer owner"),
    }
    return {name: expect_refusal(lambda: ReadXmtStages(replace_span(payload, offset, encoded), nodes, ids), error)
            for name, (offset, encoded, error) in variants.items()}


def foreign_contexts(archive, contrast):
    foreign_archive = replace(archive, records=tuple(
        replace(record, data=contrast.require(PARTITION)) if record.name == PARTITION else record
        for record in archive.records
    ))
    wrong_partition = expect_refusal(lambda: ReadFilletHist(foreign_archive),
                                    "SOLIDWORKS live fillet topology or radius differs")
    link = ReadNativeLink(archive, 0, ReadFillets=True)
    owners = ReadFilletOwn(link)
    controller = owners.Controllers[-1]
    owners.FilletValue.FieldsValue["f3d0"] = replace(controller, FieldsValue=dict(controller.FieldsValue))
    wrong_controller = expect_refusal(lambda: ReadFilletOwn(link),
                                      "through-all presentation owner does not alias its archive map")
    return {"crossed_actual_partition": wrong_partition, "detached_equal_controller": wrong_controller}


def worker(capture, control, name, edited):
    baseline = checked_json(BASELINE, BASELINE_PIN)
    if not name:
        raw = checked(control, CONTROL)
        blocked = guard_runtime()
        result = control_history(raw) | {"runtime_external_access_attempts": 0}
        require(json.loads(json.dumps(result)) == baseline["strict_control"],
                "existing strict control differs from the recorded baseline")
        explicit_refusal = expect_refusal(lambda: ReadFilletHist(SldprtArchive.from_bytes(raw)),
                                          "SOLIDWORKS fillet history needs one actual fillet root")
        require(not blocked, "strict control attempted external data access")
        return result | {"explicit_fillet_refusal": explicit_refusal}
    expected, = (row for row in baseline["results"] if row["case"] == name and row["edited"] == edited)
    raw = source(capture, expected)
    contrast = None
    if name == NAMES[0] and not edited:
        unrelated, = (row for row in baseline["results"] if row["case"] == NAMES[1] and not row["edited"])
        contrast = source(capture, unrelated)
    blocked = guard_runtime()
    archive = SldprtArchive.from_bytes(raw)
    result = ReadFilletHist(archive)
    active, delta = DecodePartData(archive.require(PARTITION), PARTITION)
    nodes = ReadActiveNodes(active.data)
    root, frames = decode_history(delta.data)
    ids = tuple(expected["selectors_from_typed_archive"])
    ordered, states = ordered_states(nodes, root, frames, ids)
    compare_stages(result, ordered, states)
    old_history = expect_refusal(lambda: ReadXmtHistory(delta.data, nodes), expected["strict_delete_profile_refusal"])
    old_link = expect_refusal(lambda: ReadNativeLink(archive, 0), "unsupported SOLIDWORKS body class Fillet_c schema 1")
    require(tuple(node.FieldsValue["f18"] for node in result.OwnersValue.Controllers) == ids
            and result.BodyIndex == expected["body_integrity"]["selected"]["body_slot"],
            "actual controller or body identity differs from the recorded proof")
    negatives = {}
    if contrast is not None:
        negatives = wire_refusals(delta.data, nodes, ids, ordered, states)
        negatives.update(foreign_contexts(archive, SldprtArchive.from_bytes(contrast)))
    require(not blocked, "fillet transaction attempted external data access")
    return {
        "source_sha256": expected["source_sha256"], "case": name, "edited": edited,
        "controller_slots": [node.IndexValue for node in result.OwnersValue.Controllers],
        "controller_mark_ids": ids, "body_slot": result.BodyIndex, "radius_m": result.RadiusValue,
        "node_counts": [len(stage.NodesValue) for stage in result.StagesValue],
        "all_rows_and_states_match": True, "refusals": negatives, "runtime_external_access_attempts": 0,
        "strict_history_refusal": old_history, "ordinary_link_refusal": old_link,
    }


def launch(args, *role):
    command = (sys.executable, "-B", str(HERE / "AuditFilletTxn.py"), "--capture", str(args.capture),
               "--control", str(args.control), *role)
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    require(process.returncode == 0 and not process.stderr, f"guarded typed transaction proof failed: {process.stderr}")
    return json.loads(process.stdout)


def main():
    parser = ArgumentParser(description="Verify the bounded SOLIDWORKS fillet production transaction")
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--report", type=Path)
    mode.add_argument("--worker", nargs=2)
    mode.add_argument("--control-worker", action="store_true")
    args = parser.parse_args()
    if args.worker or args.control_worker:
        name, phase = args.worker or (None, None)
        require(name is None or name in NAMES and phase in ("original", "edited"), "unsupported disclosed request")
        print(json.dumps(worker(args.capture, args.control, name, phase == "edited"), sort_keys=True, allow_nan=False))
        return 0
    require(not args.report.resolve().is_relative_to(args.capture.resolve()), "report must stay outside capture")
    input_custody(args.capture)
    rows = [launch(args, "--worker", name, phase) for name in NAMES for phase in ("original", "edited")]
    control = launch(args, "--control-worker")
    report = {
        "schema": "kit.sw2026.edge-fillet-transaction.v1", "oracle_build": BUILD, "oracle_sha256": ORACLE,
        "source_lock_sha256": DISCLOSED_LOCK, "physical_baseline_revision": BASELINE_REVISION,
        "physical_baseline_sha256": BASELINE_PIN, "passed": True, "results": rows, "strict_delete_control": control,
        "production_entry": "ReadFilletHist", "public_fillet_admission": False, "native_processes_started": 0,
        "private_inputs_read": 0, "writer_outputs": 0,
    }
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"typed_transactions": len(rows), "passed": True, "strict_delete_control": True,
                      "negative_cases": sum(len(row["refusals"]) for row in rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
