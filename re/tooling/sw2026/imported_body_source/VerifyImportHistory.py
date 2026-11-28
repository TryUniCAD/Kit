from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import platform
import sys
import zlib

from BuildImportedLocalPart import batch, empty_local_history
from LocalBodyEnvelope import PARTITION
from LocalBodyKernel import fingerprint, require
from convert.Geometry.Parasolid import DecodePartData, ParaHeaderData
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.Fields.WorldShapes import KWorldShapes
from convert.adapters.solidworks.Archive.Partition.ImportHistory.ImportEvent import ImportEvent
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeEmptyWorld import MakeEmptyWorld
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeImportHist import MakeImportHist
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import WriteXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from para.Partition import frame_payloads, read_partition, write_payloads
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = "src/convert/adapters/solidworks/Archive/Partition"
HOST = "re/tooling/sw2026/imported_body_source"
EVENTS = (ImportEvent.KActivation, ImportEvent.KLocalAttach)
OWNING_SOURCES = (
    *(f"{PACKAGE}/ImportHistory/{name}.py" for name in (
        "ImportEvent", "ImportHistory", "MakeImportHist", "MakeImportMarks",
        "MakeEmptyWorld", "WriteXmtEndMut", "WriteRollMut", "WriteImportHist",
    )),
    f"{PACKAGE}/LocalWrite/WriteXmtNodeMut.py", f"{PACKAGE}/Fields/WorldShapes.py",
    f"{PACKAGE}/CheckXmtMarks.py", f"{PACKAGE}/ReadXmtHistory.py", f"{PACKAGE}/ReadRollbackMut.py",
    "src/convert/Geometry/Parasolid.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/Imports/BindImportMut.py",
    f"{HOST}/BuildImportedLocalPart.py", f"{HOST}/VerifyImportHistory.py",
    "re/tooling/sw2026/para/Partition.py", "re/tooling/sw2026/para/rectangle/Allocate.py",
)


def check_fields(data):
    active, history = DecodePartData(data)
    nodes = ReadActiveNodes(active.data)
    CheckXmtGraph(nodes)
    ReadXmtHistory(history.data, nodes)
    decoded = read_partition(data)
    require(frame_payloads(write_payloads(decoded)) == data, "decoded partition changed in re-emission")
    world, = decoded.nodes
    require(world.index == 1 and world.kind == 101 and world.fields["alive"] == 1
            and world.fields["current_id"] == world.fields["highest_id"] and not world.fields["body"]
            and all(not value for field, value in world.fields.items()
                    if field not in ("alive", "current_id", "highest_id")), "active world has unexpected state")
    entries = []
    for item in decoded.history:
        fields = item.mark.fields
        preceding = item.rollback.previous_world if item.rollback else None
        require(not item.rollback or not item.rollback.deleted and
                not any(value for field, value in preceding.fields.items() if field != "alive"),
                "rollback world carried a body, map, mark or deletion")
        entries.append({
            "index": item.mark.index,
            "mark_id": fields["id"],
            "delta_key": fields["delta_key"],
            "preceding_index": fields["preceding"],
            "following_index": fields["first_following"],
            "previous_world_alive": preceding.fields["alive"] if preceding else None,
        })
    require(tuple(row["previous_world_alive"] for row in entries) == (1, None, 0),
            "retained worlds disagree with activation and selected roles")
    return {
        "active_world": {**world.fields, "index": world.index},
        "partition_root": {**decoded.root.fields, "index": decoded.root.index},
        "history_transmit_order": entries,
        "frames": [
            {
                "role": ParaHeaderData(frame.data).description,
                "uncompressed": fingerprint(frame.data),
                "stored_size": frame.stored_size,
            }
            for frame in (active, history)
        ],
    }


def check_models(candidate):
    parts, denied = batch(PureWindowsPath("C:/KitImportHistoryProof"), completed=True)
    require(not denied and len(parts) == 4, "fresh import model scope or guarded access changed")
    cases = {}
    for name, (blob, _) in parts.items():
        archive = SldprtArchive.from_bytes(blob)
        require(archive.require(PARTITION) == candidate.BytesValue, "fresh model differs at its complete partition")
        link = ReadNativeLink(archive, 0)
        imported, = (
            node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moBaseBody_c"
        )
        activation = link.ConfigValue.RootValue.FieldsValue["fe38"].FieldsValue["f18"]
        selected = imported.FieldsValue["f3d0"].FieldsValue["f18"]
        require((activation, selected) == candidate.MarkIds, "native archive owners reference different marks")
        cases[name] = {
            "part": fingerprint(blob),
            "complete_partition_matches": True,
            "model_activation_mark": activation,
            "import_selected_mark": selected,
        }
    return cases


def must_refuse(name, action, *arguments):
    try:
        action(*arguments)
    except ValueError as error:
        return str(error)
    raise ValueError("invalid import history was accepted: " + name)


def refusals():
    candidates = {
        "earlier_archive": (18000, EVENTS),
        "no_local_attachment": (19000, EVENTS[:1]),
        "no_activation": (19000, EVENTS[1:]),
        "blank_event_plan": (19000, ()),
        "attachment_before_activation": (19000, EVENTS[::-1]),
        "second_local_attachment": (19000, EVENTS + EVENTS[1:]),
        "duplicated_activation": (19000, (EVENTS[0], EVENTS[0])),
        "untyped_events": (19000, tuple(event.value for event in EVENTS)),
        "mutable_events": (19000, list(EVENTS)),
        "approximate_archive_version": (19000.0, EVENTS),
    }
    result = {name: must_refuse(name, MakeImportHist, *arguments) for name, arguments in candidates.items()}
    world = MakeEmptyWorld(1, 1, 0)
    for name, value in {
        "body_in_preceding_world": replace(world, FieldsValue={**world.FieldsValue, "body": 12}),
        "active_mark_in_preceding_world": MakeEmptyWorld(1, 1, 3),
        "invalid_preceding_alive": MakeEmptyWorld(1, 2, 0),
        "foreign_preceding_world_index": MakeEmptyWorld(2, 1, 0),
    }.items():
        output, kinds = bytearray(), set()
        result[name] = must_refuse(
            name, lambda node: WriteXmtNodeMut(output, node, KWorldShapes[101], kinds, PreviousWorld=True), value
        )
        require(not output and not kinds, "invalid preceding world mutated writer state")
    return result


def verify():
    for name in ("utf-16-le", "utf-8", "latin-1"):
        lookup(name)
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    enabled = True

    def guard(event, arguments):
        if enabled:
            audit.InspectEvent(event, arguments)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError("local import history attempted " + event)

    sys.addaudithook(guard)
    try:
        legacy_marks, legacy = empty_local_history()
        candidate = MakeImportHist(19000, EVENTS)
        require(candidate.BytesValue == legacy and
                candidate.MarkIds == (legacy_marks.activation.mark_id, legacy_marks.selected.mark_id),
                "package import history differs from its independent fresh reference")
        field_values = check_fields(candidate.BytesValue)
        cases = check_models(candidate)
        refused = refusals()
    finally:
        enabled = False
    require(not audit.DeniedReads, "import history construction attempted runtime access")
    return {
        "schema": "kit.sw2026.package-import-history.v1",
        "version": 19000,
        "input_events": tuple(event.value for event in EVENTS),
        "mark_ids_in_archive_binding_order": candidate.MarkIds,
        "complete_stream": fingerprint(candidate.BytesValue),
        "fresh_reference_exact": True,
        "decoded_fields": field_values,
        "fresh_parts": cases,
        "refusals": refused,
        "guarded_file_reads": len(audit.DeniedReads),
        "input_saved_part_count": 0,
        "native_application_launches": 0,
        "saved_native_output_files": 0,
        "native_acceptance": False,
        "source_sha256": {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in OWNING_SOURCES},
        "runtime": {"python": platform.python_version(), "zlib": zlib.ZLIB_RUNTIME_VERSION},
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True, allow_nan=False))
