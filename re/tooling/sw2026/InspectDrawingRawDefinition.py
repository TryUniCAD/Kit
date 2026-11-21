from __future__ import annotations

import sys
from pathlib import Path

sys.path[:] = [
    value
    for value in sys.path
    if Path(value or ".").resolve() != Path(__file__).resolve().parent
]

import argparse
from collections import Counter
from functools import partial
import hashlib
import json


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_code(candidate, expected):
    path = candidate / "SourceManifest.json"
    if digest(path) != expected:
        raise ValueError("reader manifest differs from frozen identity")
    manifest = json.loads(path.read_bytes())
    names = []
    for row in manifest["files"]:
        source = candidate / "CodeRoot" / row["path"]
        data = source.read_bytes()
        if (
            len(data) != row["bytes"]
            or hashlib.sha256(data).hexdigest() != row["sha256"]
        ):
            raise ValueError("frozen reader source changed: " + row["path"])
        names.append(row["path"])
    if len(names) != manifest["file_count"] or len(set(names)) != len(names):
        raise ValueError("reader closure membership is inconsistent")
    return manifest


def map_report(snapshot, node_type, class_type, external_type):
    rows = []
    objects = {}
    for entry in snapshot.EntriesValue:
        value = entry.EntryValue
        if isinstance(value, node_type):
            descriptor = value.ClassValue
            rows.append(
                {
                    "slot": entry.IndexValue,
                    "kind": "object",
                    "class": descriptor.NameValue,
                    "schema": (
                        descriptor.SchemaValue
                        if isinstance(descriptor, class_type)
                        else None
                    ),
                    "concrete_class": isinstance(descriptor, class_type),
                }
            )
            objects[entry.IndexValue] = value
        elif isinstance(value, class_type):
            rows.append(
                {
                    "slot": entry.IndexValue,
                    "kind": "class",
                    "class": value.NameValue,
                    "schema": value.SchemaValue,
                }
            )
        elif isinstance(value, external_type):
            rows.append(
                {
                    "slot": entry.IndexValue,
                    "kind": "external_class",
                    "class": value.NameValue,
                    "schema": None,
                }
            )
        else:
            raise TypeError("unrecognized archive map entry")
    rows.sort(key=lambda row: row["slot"])
    return {"counter": snapshot.CounterValue, "entries": rows}, objects


def main():
    parser = argparse.ArgumentParser(
        description="Measure raw SDK drawing Definition grammar independently of unchanged semantic admission"
    )
    parser.add_argument("candidate", type=Path)
    parser.add_argument("access_manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--access-sha256", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("output must be unused")
    manifest = verify_code(args.candidate, args.manifest_sha256)
    if digest(args.access_manifest) != args.access_sha256:
        raise ValueError("disclosed source custody manifest changed")
    code = args.candidate / "CodeRoot"
    sys.path[:0] = [str(code / "src"), str(code)]

    from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
    from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
    from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
    from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
    from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
    from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
    from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import (
        ReadFieldsMut,
    )
    from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
        ReadSchemaMut,
    )
    from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
    from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
    from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import (
        WriteFieldsMut,
    )
    from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
        WriteSchemaMut,
    )
    from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import (
        KDefPrefixFields,
    )
    from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
    from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
    from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Drawing.Definition.Emission.ReadDrawMut import (
        ReadDrawMut,
    )
    from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import (
        WalkDrawNodes,
    )
    from convert.adapters.solidworks.Drawing.Definition.Emission.WriteDrawMut import (
        WriteDrawMut,
    )
    from convert.adapters.solidworks.Drawing.Definition.Linked.BindFrontMut import (
        BindFrontMut,
    )
    from convert.adapters.solidworks.Drawing.Definition.Linked.FrontLayouts import (
        KFrontLayouts,
    )
    from convert.adapters.solidworks.Drawing.Definition.Linked.FrontSchemas import (
        KFrontSchemas,
    )
    from convert.adapters.solidworks.Drawing.Definition.Linked.FrontVirtuals import (
        KFrontVirtuals,
    )
    from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import (
        ReadNamedDef,
    )
    from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid

    def new_context():
        value = BodyContext(19000, KFrontLayouts, KFrontVirtuals, KFrontSchemas)
        value.FlagsValue["owner_is_drawing"] = 1
        return value

    def raw_store_node(writer, node):
        descriptor = node.ClassValue
        if (
            isinstance(descriptor, RuntimeClass)
            and (descriptor.NameValue, descriptor.SchemaValue) in KHeaderClasses
        ):
            WriteDrawMut(writer, node)
        else:
            WriteBodyMut(writer, node)

    expected = {
        "H01SheetA": (
            "8fca05f17d7a331da70daf83a189be6dacc6f2cfc946d452b0c246a8ddab0b6b",
            "*Right",
        ),
        "H02SheetB": (
            "b21216652ce759bc6e4912b0116eeb7bd78de4ba456f19f83449e56010663b77",
            "*Top",
        ),
    }
    access = json.loads(args.access_manifest.read_bytes())
    result = {
        "schema": "kit.sw2026.drawing-raw-grammar-inspection.v1",
        "reader_manifest_sha256": args.manifest_sha256,
        "access_manifest_sha256": args.access_sha256,
        "reader_source_files": manifest["file_count"],
        "runner_sha256": digest(Path(__file__)),
        "original_frozen_writer_manifest_sha256": manifest[
            "base_frozen_writer_manifest_sha256"
        ],
        "native_proof_sha256": manifest["native_proof_sha256"],
        "scope": "raw field grammar and graph maps only; normal semantic guard remains unchanged",
        "cases": [],
        "normal_sdk_guard_changed": False,
        "new_public_mode": False,
        "complete_source_semantics_admitted": False,
        "native_execution": False,
        "vm_access": False,
        "test_suite_execution": False,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "original_heldout_verdict_changed": False,
        "writer_source_changed": False,
        "source_saved_byte_fallback": False,
        "output_definition_saved_as_cad_file": False,
    }
    for entry in access["files"]:
        source = Path(entry["path"])
        if source.suffix.upper() != ".SLDDRW":
            continue
        if source.stem not in expected or entry["sha256"] != expected[source.stem][0]:
            raise ValueError("source is not one of the two exactly disclosed originals")
        source_data = source.read_bytes()
        if hashlib.sha256(source_data).hexdigest() != entry["sha256"]:
            raise ValueError("disclosed original bytes changed")
        data = SldprtArchive.from_bytes(source_data).require("Contents/Definition")
        row = {
            "case": source.stem,
            "input_sha256": entry["sha256"],
            "stream": "Contents/Definition",
            "stream_bytes": len(data),
            "stream_sha256": hashlib.sha256(data).hexdigest(),
            "raw_byte_round_trip_passed": False,
            "raw_load_complete": False,
            "raw_store_complete": False,
            "normal_semantic_admission": False,
        }
        try:
            ReadNamedDef(data, 19000, expected[source.stem][1])
        except Exception as error:
            row["normal_reader_rejection"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
        else:
            row["normal_semantic_admission"] = True

        load_context = new_context()
        store_context = new_context()
        cursor = BinaryReader(data)
        reader = GraphReader(cursor, ArchiveMaps(1), partial(ReadDrawMut, load_context))
        document = ArchiveNode(RuntimeClass("uiDrawingDoc_c", 1), {})
        writer = None
        phase = "raw prefix load"
        try:
            frame = ReadFrame(
                load_context,
                reader,
                FieldScope(document.FieldsValue),
                document,
                ReadSchemaMut,
                ReadFieldsMut,
            )
            ReadFieldsMut(frame, KDefPrefixFields)
            clsid = cursor.TakeBytes(len(KDrawClsid))
            if clsid != KDrawClsid:
                raise ValueError("raw drawing document clsid differs")
            document.FieldsValue.update(
                clsid_a=int.from_bytes(clsid[:4], "little"),
                clsid_b=int.from_bytes(clsid[4:6], "little"),
                clsid_c=int.from_bytes(clsid[6:8], "little"),
                clsid_d=clsid[8:],
            )
            phase = "raw body load"
            ReadBodyMut(load_context, reader, document)
            row["unread_tail_bytes"] = cursor.GetRemaining()
            if cursor.GetRemaining() != 0:
                raise ValueError("raw drawing grammar left an unread tail")
            load_context.UsageValue.IsComplete = True
            row["raw_load_complete"] = True
            row["ui_guard_selectors"] = {
                name: document.FieldsValue[name]
                for name in ("has_pwmaterial", "drawing_end_marker")
            }
            phase = "derived runtime owner binding"
            BindFrontMut(document)
            row["runtime_owner_binding_complete"] = True
            read_map = reader.MapValue.Snapshot()
            phase = "raw prefix store"
            writer = BodyWriter(ArchiveMaps(1), store_context, raw_store_node)
            frame = WriteFrame(
                writer,
                FieldScope(document.FieldsValue),
                document,
                WriteSchemaMut,
                WriteFieldsMut,
            )
            WriteFieldsMut(frame, KDefPrefixFields)
            writer.OutputValue.extend(KDrawClsid)
            phase = "raw body store"
            WriteBodyMut(writer, document)
            store_context.UsageValue.IsComplete = True
            row["raw_store_complete"] = True
            output = bytes(writer.OutputValue)
            phase = "raw map and byte comparison"
            read_report, read_objects = map_report(
                read_map, ArchiveNode, RuntimeClass, ExternalClass
            )
            write_report, write_objects = map_report(
                writer.MapValue.Snapshot(), ArchiveNode, RuntimeClass, ExternalClass
            )
            same_slots = read_report == write_report
            same_objects = read_objects.keys() == write_objects.keys() and all(
                read_objects[index] is write_objects[index] for index in read_objects
            )
            row.update(
                output_bytes=len(output),
                output_sha256=hashlib.sha256(output).hexdigest(),
                maps={"load": read_report, "store": write_report},
                map_slots_equal=same_slots,
                same_object_identities=same_objects,
                class_counts=dict(
                    sorted(
                        Counter(
                            node.ClassValue.NameValue
                            for node in WalkDrawNodes(document)
                        ).items()
                    )
                ),
                raw_byte_round_trip_passed=output == data
                and same_slots
                and same_objects,
            )
            if output != data:
                row["first_mismatch_offset"] = next(
                    (
                        index
                        for index, pair in enumerate(zip(data, output))
                        if pair[0] != pair[1]
                    ),
                    min(len(data), len(output)),
                )
        except Exception as error:
            row["raw_failure"] = {
                "phase": phase,
                "type": type(error).__name__,
                "message": str(error),
            }
        row["load_usage"] = dict(GetBodyReport(load_context.UsageValue))
        row["store_usage"] = dict(GetBodyReport(store_context.UsageValue))
        row["cursor_offset"] = cursor.GetOffset()
        row["remaining_bytes"] = cursor.GetRemaining()
        row["input_unchanged"] = digest(source) == entry["sha256"]
        row["normal_rejection_retained"] = (
            row.get("normal_reader_rejection", {}).get("message")
            == "blank drawing Definition has unqualified ui state"
        )
        row["complete_source_semantics_admitted"] = False
        row["native_acceptance"] = False
        row["heldout_acceptance"] = False
        result["cases"].append(row)
    if [row["case"] for row in result["cases"]] != ["H01SheetA", "H02SheetB"]:
        raise ValueError("exactly the two disclosed drawings must be inspected")
    _ = verify_code(args.candidate, args.manifest_sha256)
    if digest(args.access_manifest) != args.access_sha256:
        raise ValueError("disclosed source custody changed during measurement")
    result["source_immutable"] = True
    result["raw_only_passed"] = all(
        row["raw_byte_round_trip_passed"]
        and row["raw_load_complete"]
        and row["raw_store_complete"]
        and row["normal_rejection_retained"]
        and not row["normal_semantic_admission"]
        and row["input_unchanged"]
        and not row["load_usage"]["missing_schemas"]
        and not row["store_usage"]["missing_schemas"]
        for row in result["cases"]
    )
    payload = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    with args.output.open("x", encoding="utf-8") as target:
        target.write(payload)
    print(
        json.dumps(
            {
                "raw_only_passed": result["raw_only_passed"],
                "normal_rejections_retained": [
                    row["normal_rejection_retained"] for row in result["cases"]
                ],
                "raw_failures": [row.get("raw_failure") for row in result["cases"]],
                "report_sha256": digest(args.output),
                "complete_source_semantics_admitted": False,
                "heldout_acceptance": False,
            }
        )
    )
    return 0 if result["raw_only_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
