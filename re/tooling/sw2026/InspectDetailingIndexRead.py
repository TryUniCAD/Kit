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
from collections.abc import Mapping
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
    parser.add_argument("--generated-control", type=Path, required=True)
    parser.add_argument("--control-sha256", required=True)
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
    from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import (
        BodyUnsupported,
    )
    from convert.adapters.solidworks.Drawing.Definition.Detailing.ReadDetailMap import (
        ReadDetailMap,
    )
    from convert.adapters.solidworks.Drawing.Definition.Named.NamedGraph import (
        NamedGraph,
    )
    from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import (
        WriteNamedDef,
    )

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

    def inspect_detail(document):
        model = document.FieldsValue["model"]
        actual = ReadDetailMap(model, 19000)
        raw_groups = model.FieldsValue["f1570"]
        groups = []
        same_aliases = actual.ModelValue is model and len(actual.GroupsValue) == len(
            raw_groups
        )
        for group_index, group in enumerate(actual.GroupsValue):
            raw = raw_groups[group_index]
            rows = []
            same_aliases = same_aliases and len(group.RowsValue) == len(raw["rows"])
            for row_index, row in enumerate(group.RowsValue):
                retained = raw["rows"][row_index]
                reference = row.RefValue
                same = reference is retained["ref"]
                same_aliases = same_aliases and same
                rows.append(
                    {
                        "component_key": row.ComponentKey,
                        "downstream_id_u32": row.DownstreamId,
                        "wire_key_i32": retained["key"],
                        "reference_object_index": reference.IndexValue,
                        "reference_class": reference.ClassValue.NameValue,
                        "reference_schema": reference.ClassValue.SchemaValue,
                        "same_raw_reference_object": same,
                        "entity_reference_count": reference.FieldsValue["f08"],
                        "feature_persistent_id_inferred_from_f08": False,
                    }
                )
            groups.append(
                {
                    "model_key": group.ModelKey,
                    "declared_rows": raw["n"],
                    "actual_rows": len(rows),
                    "rows": rows,
                }
            )
        return {
            "declared_sections": model.FieldsValue["n1578"],
            "actual_sections": len(groups),
            "groups": groups,
            "unprojected": list(actual.Unprojected),
            "raw_reference_aliases_preserved": same_aliases,
            "source_fields_mutated": False,
            "portable_edge_resolution_claimed": False,
            "prior_generic_f08_label_corrected": "moBEntRef f08 is entity count, not a feature persistent id",
        }

    def inspect_negatives(document, orientation):
        model = document.FieldsValue["model"]
        fields = model.FieldsValue
        original = fields["f1570"]
        original_count = fields["n1578"]
        if not original or not original[0]["rows"]:
            raise ValueError(
                "disclosed map needs real rows before malformed component checks"
            )
        names = [
            "missing outer rows",
            "outer negative count",
            "outer count mismatch",
            "outer boolean count",
            "invalid section mapping",
            "invalid model text",
            "inner negative count",
            "inner count mismatch",
            "inner boolean count",
            "missing inner rows",
            "invalid component text",
            "zero downstream id",
            "downstream below signed32",
            "downstream above signed32",
            "boolean downstream id",
            "null edge reference",
            "same name external reference",
            "wrong edge schema",
            "wrong reference class",
            "duplicate component id",
            "duplicate model key",
            "invalid row mapping",
            "missing edge reference",
        ]
        results = []
        graph = NamedGraph(document, 19000, orientation)
        for name in names:
            changed = [
                dict(section, rows=[dict(row) for row in section["rows"]])
                for section in original
            ]
            fields["f1570"] = changed
            fields["n1578"] = original_count
            group = changed[0]
            item = group["rows"][0]
            if name == "missing outer rows":
                fields["f1570"] = None
            elif name == "outer negative count":
                fields["n1578"] = -1
            elif name == "outer count mismatch":
                fields["n1578"] = original_count + 1
            elif name == "outer boolean count":
                fields["n1578"] = True
            elif name == "invalid section mapping":
                changed[0] = None
            elif name == "invalid model text":
                group["file"] = 12
            elif name == "inner negative count":
                group["n"] = -1
            elif name == "inner count mismatch":
                group["n"] += 1
            elif name == "inner boolean count":
                group["n"] = False
            elif name == "missing inner rows":
                group["rows"] = None
            elif name == "invalid component text":
                item["name"] = None
            elif name == "zero downstream id":
                item["key"] = 0
            elif name == "downstream below signed32":
                item["key"] = -(1 << 31) - 1
            elif name == "downstream above signed32":
                item["key"] = 1 << 31
            elif name == "boolean downstream id":
                item["key"] = True
            elif name == "null edge reference":
                item["ref"] = None
            elif name == "same name external reference":
                item["ref"] = ArchiveNode(ExternalClass("moEdgeRef_c", 1), {})
            elif name == "wrong edge schema":
                item["ref"] = ArchiveNode(RuntimeClass("moEdgeRef_c", 2), {})
            elif name == "wrong reference class":
                item["ref"] = ArchiveNode(RuntimeClass("moVertexRef_c", 1), {})
            elif name == "duplicate component id":
                group["rows"].append(dict(item))
                group["n"] += 1
            elif name == "duplicate model key":
                changed.append(dict(group, rows=[dict(row) for row in group["rows"]]))
                fields["n1578"] += 1
            elif name == "invalid row mapping":
                group["rows"][0] = None
            elif name == "missing edge reference":
                item.pop("ref")
            try:
                WriteNamedDef(graph)
            except Exception as error:
                rejected = isinstance(error, BodyUnsupported) and str(error).startswith(
                    "drawing detailing index"
                )
                results.append(
                    {
                        "case": name,
                        "rejected_by_typed_index": rejected,
                        "exception": type(error).__name__,
                        "message": str(error),
                        "result_returned": False,
                    }
                )
            else:
                results.append(
                    {
                        "case": name,
                        "rejected_by_typed_index": False,
                        "result_returned": True,
                    }
                )
            finally:
                fields["f1570"] = original
                fields["n1578"] = original_count
        return results

    if digest(args.generated_control) != args.control_sha256:
        raise ValueError("generated empty map control changed")
    control_data = SldprtArchive.from_bytes(
        args.generated_control.read_bytes()
    ).require("Contents/Definition")
    control_read = ReadNamedDef(control_data, 19000, "*Front")
    control_written = WriteNamedDef(control_read.GraphValue)
    control = {
        "input_sha256": args.control_sha256,
        "definition_sha256": hashlib.sha256(control_data).hexdigest(),
        "normal_read_passed": True,
        "normal_store_byte_identical": control_written.OutputValue == control_data,
        "unprojected": list(control_read.Unprojected),
        "typed_sections": len(control_read.DetailingMap.GroupsValue),
        "alias_owner_is_actual_model": control_read.DetailingMap.ModelValue
        is control_read.GraphValue.DocumentValue.FieldsValue["model"],
        "input_producer": "SDK generated disclosed Front control",
    }
    if (
        not control["normal_store_byte_identical"]
        or control["unprojected"]
        or control["typed_sections"] != 0
        or not control["alias_owner_is_actual_model"]
    ):
        raise ValueError("existing qualified empty index behavior changed")

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
        "schema": "kit.sw2026.drawing-detailing-index-process.v1",
        "reader_manifest_sha256": args.manifest_sha256,
        "access_manifest_sha256": args.access_sha256,
        "reader_source_files": manifest["file_count"],
        "runner_sha256": digest(Path(__file__)),
        "original_frozen_writer_manifest_sha256": manifest[
            "base_frozen_writer_manifest_sha256"
        ],
        "native_proof_sha256": manifest["native_proof_sha256"],
        "scope": "typed native detailing keys, reference identities and unprojected state plus complete raw byte/map preservation; later annotation guard remains unchanged",
        "generated_empty_index_control": control,
        "cases": [],
        "later_semantic_guards_changed": False,
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
            "normal_definition_admission": False,
        }
        try:
            ReadNamedDef(data, 19000, expected[source.stem][1])
        except Exception as error:
            row["normal_reader_rejection"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
        else:
            row["normal_definition_admission"] = True

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
            row["typed_detailing_index"] = inspect_detail(document)
            row["malformed_index_cases"] = inspect_negatives(
                document, expected[source.stem][1]
            )
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
            == "named drawing Definition excludes unqualified annotation and display payloads"
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
    result["generated_control_unchanged"] = (
        digest(args.generated_control) == args.control_sha256
    )
    result["raw_only_passed"] = result["generated_control_unchanged"] and all(
        row["raw_byte_round_trip_passed"]
        and row["raw_load_complete"]
        and row["raw_store_complete"]
        and row["normal_rejection_retained"]
        and not row["normal_definition_admission"]
        and row.get("typed_detailing_index", {}).get("raw_reference_aliases_preserved")
        is True
        and row.get("typed_detailing_index", {}).get("unprojected")
        == ["drawing.detailing_edges"]
        and len(row.get("malformed_index_cases", ())) == 23
        and all(
            case["rejected_by_typed_index"] and not case["result_returned"]
            for case in row["malformed_index_cases"]
        )
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
