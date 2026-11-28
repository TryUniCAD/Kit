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
        description="Measure typed drawing view cache and native occurrence colours through the real Definition read and store boundary"
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

    from convert.adapters.solidworks.Drawing.Definition.Rendering.ReadGraphRender import (
        ReadGraphRender,
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

    def inspect_render(document):
        actual = ReadGraphRender(document, 19000)
        fields = actual.ViewValue.FieldsValue
        retained = fields["ff60"]
        rows = [
            {
                "occurrence_number_i32": row.OccurrenceNum,
                "colour_word_u32": row.ColourWord,
            }
            for row in actual.ColoursValue
        ]
        same_rows = len(rows) == len(retained) and all(
            row["occurrence_number_i32"] == raw["key"]
            and row["colour_word_u32"] == raw["value"]
            for row, raw in zip(rows, retained)
        )
        return {
            "actual_view_object_index": actual.ViewValue.IndexValue,
            "concrete_view_class": actual.ViewValue.ClassValue.NameValue,
            "concrete_view_schema": actual.ViewValue.ClassValue.SchemaValue,
            "cache_present": actual.CachePresent,
            "saved_cache_count": actual.SavedCacheCount,
            "source_cache_presence": fields["has_fb50"],
            "source_cache_payload": fields.get("fb50"),
            "declared_colour_count": fields.get("nf68", len(retained)),
            "actual_colour_count": len(rows),
            "colour_rows": rows,
            "native_colour_rows_preserved": same_rows,
            "unprojected": list(actual.Unprojected),
            "component_colour_join_projected": False,
            "colour_rgb_encoding_claimed": False,
            "source_fields_mutated": False,
        }

    def inspect_negatives(document, orientation):
        actual = ReadGraphRender(document, 19000)
        fields = actual.ViewValue.FieldsValue
        original = {
            name: fields.get(name) for name in ("has_fb50", "fb50", "nf68", "ff60")
        }
        original_keys = set(fields)
        names = [
            "missing cache presence",
            "null cache presence",
            "boolean cache presence",
            "negative cache presence",
            "noncanonical cache presence",
            "missing present cache",
            "invalid cache mapping",
            "missing cache count",
            "boolean cache count",
            "negative cache count",
            "populated cache count",
            "unknown cache field",
            "absent cache with payload",
            "missing colour rows",
            "invalid colour rows",
            "negative colour count",
            "boolean colour count",
            "mismatched colour count",
            "oversized colour count",
            "invalid colour row",
            "missing occurrence key",
            "missing colour word",
            "unknown colour field",
            "boolean occurrence key",
            "occurrence below signed32",
            "occurrence above signed32",
            "boolean colour word",
            "colour below unsigned32",
            "colour above unsigned32",
            "duplicate occurrence key",
        ]
        graph = NamedGraph(document, 19000, orientation)
        results = []
        for name in names:
            fields.update(original)
            fields["has_fb50"] = 1
            fields["fb50"] = {"n": 0}
            fields["nf68"] = 1
            fields["ff60"] = [{"key": 7, "value": 0x01020304}]
            item = fields["ff60"][0]
            if name == "missing cache presence":
                fields.pop("has_fb50")
            elif name == "null cache presence":
                fields["has_fb50"] = None
            elif name == "boolean cache presence":
                fields["has_fb50"] = True
            elif name == "negative cache presence":
                fields["has_fb50"] = -1
            elif name == "noncanonical cache presence":
                fields["has_fb50"] = 2
            elif name == "missing present cache":
                fields.pop("fb50")
            elif name == "invalid cache mapping":
                fields["fb50"] = None
            elif name == "missing cache count":
                fields["fb50"] = {}
            elif name == "boolean cache count":
                fields["fb50"] = {"n": False}
            elif name == "negative cache count":
                fields["fb50"] = {"n": -1}
            elif name == "populated cache count":
                fields["fb50"] = {"n": 1}
            elif name == "unknown cache field":
                fields["fb50"] = {"n": 0, "items": []}
            elif name == "absent cache with payload":
                fields["has_fb50"] = 0
            elif name == "missing colour rows":
                fields.pop("ff60")
            elif name == "invalid colour rows":
                fields["ff60"] = None
            elif name == "negative colour count":
                fields["nf68"] = -1
            elif name == "boolean colour count":
                fields["nf68"] = True
            elif name == "mismatched colour count":
                fields["nf68"] = 2
            elif name == "oversized colour count":
                fields["nf68"] = 1 << 31
            elif name == "invalid colour row":
                fields["ff60"] = [None]
            elif name == "missing occurrence key":
                item.pop("key")
            elif name == "missing colour word":
                item.pop("value")
            elif name == "unknown colour field":
                item["unknown"] = 0
            elif name == "boolean occurrence key":
                item["key"] = True
            elif name == "occurrence below signed32":
                item["key"] = -(1 << 31) - 1
            elif name == "occurrence above signed32":
                item["key"] = 1 << 31
            elif name == "boolean colour word":
                item["value"] = True
            elif name == "colour below unsigned32":
                item["value"] = -1
            elif name == "colour above unsigned32":
                item["value"] = 1 << 32
            elif name == "duplicate occurrence key":
                fields["ff60"].append(dict(item))
                fields["nf68"] = 2
            try:
                wire = WriteNamedDef(graph)
            except Exception as error:
                results.append(
                    {
                        "case": name,
                        "rejected_by_typed_view_state": isinstance(
                            error, BodyUnsupported
                        )
                        and str(error).startswith("drawing view state"),
                        "exception": type(error).__name__,
                        "message": str(error),
                        "result_returned": False,
                    }
                )
            else:
                results.append(
                    {
                        "case": name,
                        "rejected_by_typed_view_state": False,
                        "result_returned": True,
                        "unexpected_output_bytes": len(wire.OutputValue),
                    }
                )
            finally:
                for field in original:
                    if field in original_keys:
                        fields[field] = original[field]
                    else:
                        fields.pop(field, None)
        return results

    def inspect_modeled(document, orientation):
        actual = ReadGraphRender(document, 19000)
        fields = actual.ViewValue.FieldsValue
        original = {
            name: fields.get(name) for name in ("has_fb50", "fb50", "nf68", "ff60")
        }
        original_keys = set(fields)
        variants = [
            ("explicit absent empty cache", 0, None, []),
            ("explicit present empty cache", 1, {"n": 0}, []),
            (
                "authored signed keys and unsigned words",
                1,
                {"n": 0},
                [
                    {"key": -(1 << 31), "value": 0},
                    {"key": 0, "value": 1 << 31},
                    {"key": (1 << 31) - 1, "value": (1 << 32) - 1},
                ],
            ),
        ]
        results = []
        for name, presence, cache, colours in variants:
            try:
                fields.update(
                    has_fb50=presence, fb50=cache, nf68=len(colours), ff60=colours
                )
                first = WriteNamedDef(NamedGraph(document, 19000, orientation))
                loaded = ReadNamedDef(first.OutputValue, 19000, orientation)
                second = WriteNamedDef(loaded.GraphValue)
                retained = inspect_render(loaded.GraphValue.DocumentValue)
                results.append(
                    {
                        "case": name,
                        "output_bytes": len(first.OutputValue),
                        "output_sha256": hashlib.sha256(first.OutputValue).hexdigest(),
                        "read_store_byte_identical": first.OutputValue
                        == second.OutputValue,
                        "retained_rendering": retained,
                        "cache_presence_preserved": retained["source_cache_presence"]
                        == presence,
                        "cache_count_preserved": retained["saved_cache_count"]
                        == (0 if presence else None),
                        "colour_rows_preserved": retained["colour_rows"]
                        == [
                            {
                                "occurrence_number_i32": row["key"],
                                "colour_word_u32": row["value"],
                            }
                            for row in colours
                        ],
                        "authored_variant_not_native_measurement": True,
                    }
                )
            except Exception as error:
                results.append(
                    {
                        "case": name,
                        "failure": {
                            "type": type(error).__name__,
                            "message": str(error),
                        },
                    }
                )
            finally:
                for field in original:
                    if field in original_keys:
                        fields[field] = original[field]
                    else:
                        fields.pop(field, None)
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
        "rendering": inspect_render(control_read.GraphValue.DocumentValue),
        "result_property_uses_actual_view": control_read.Rendering.ViewValue
        is ReadGraphRender(control_read.GraphValue.DocumentValue, 19000).ViewValue,
        "alias_owner_is_actual_model": control_read.DetailingMap.ModelValue
        is control_read.GraphValue.DocumentValue.FieldsValue["model"],
        "input_producer": "SDK generated disclosed Front control",
    }
    if (
        not control["normal_store_byte_identical"]
        or control["unprojected"]
        or control["typed_sections"] != 0
        or not control["alias_owner_is_actual_model"]
        or control["rendering"]["cache_present"]
        or control["rendering"]["actual_colour_count"] != 0
        or not control["result_property_uses_actual_view"]
    ):
        raise ValueError("existing qualified empty index behavior changed")

    modeled_control = inspect_modeled(control_read.GraphValue.DocumentValue, "*Front")
    control["graph_fields_restored_after_variants"] = (
        WriteNamedDef(control_read.GraphValue).OutputValue == control_data
    )

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
        "schema": "kit.sw2026.drawing-view-render-state-process.v1",
        "reader_manifest_sha256": args.manifest_sha256,
        "access_manifest_sha256": args.access_sha256,
        "reader_source_files": manifest["file_count"],
        "runner_sha256": digest(Path(__file__)),
        "original_frozen_writer_manifest_sha256": manifest[
            "base_frozen_writer_manifest_sha256"
        ],
        "native_proof_sha256": manifest["native_proof_sha256"],
        "scope": "actual cache presence and zero saved records plus native occurrence-colour keys and words; portable component association remains explicitly unprojected",
        "generated_empty_index_control": control,
        "modeled_control_cases": modeled_control,
        "cases": [],
        "two_explained_view_predicates_replaced": [
            "has_fb50_equals_zero",
            "ff60_empty",
        ],
        "remaining_view_predicates_unchanged": 29,
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
        normal = None
        try:
            normal = ReadNamedDef(data, 19000, expected[source.stem][1])
        except Exception as error:
            row["normal_reader_rejection"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
        else:
            row["normal_definition_admission"] = True
            written = WriteNamedDef(normal.GraphValue)
            normal_load_map, normal_load_objects = map_report(
                normal.MapValue, ArchiveNode, RuntimeClass, ExternalClass
            )
            normal_store_map, normal_store_objects = map_report(
                written.MapValue, ArchiveNode, RuntimeClass, ExternalClass
            )
            row["normal_definition_read_store"] = {
                "output_bytes": len(written.OutputValue),
                "output_sha256": hashlib.sha256(written.OutputValue).hexdigest(),
                "byte_identical": written.OutputValue == data,
                "map_slots_equal": normal_load_map == normal_store_map,
                "same_object_identities": normal_load_objects.keys()
                == normal_store_objects.keys()
                and all(
                    normal_load_objects[index] is normal_store_objects[index]
                    for index in normal_load_objects
                ),
                "unprojected": list(normal.Unprojected),
                "rendering": inspect_render(normal.GraphValue.DocumentValue),
                "result_property_uses_actual_view": normal.Rendering.ViewValue
                is ReadGraphRender(normal.GraphValue.DocumentValue, 19000).ViewValue,
            }

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
            row["typed_view_rendering"] = inspect_render(document)
            row["malformed_render_cases"] = inspect_negatives(
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
        row["sheet_annotation_rejection_retained"] = (
            row.get("normal_reader_rejection", {}).get("message")
            == "blank drawing Definition excludes sheet annotations"
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
    result["typed_view_state_passed"] = (
        result["generated_control_unchanged"]
        and control["graph_fields_restored_after_variants"]
        and len(modeled_control) == 3
        and all(
            case.get("read_store_byte_identical")
            and case.get("cache_presence_preserved")
            and case.get("cache_count_preserved")
            and case.get("colour_rows_preserved")
            for case in modeled_control
        )
        and all(
            row["raw_byte_round_trip_passed"]
            and row["raw_load_complete"]
            and row["raw_store_complete"]
            and not row["normal_definition_admission"]
            and row["sheet_annotation_rejection_retained"]
            and row.get("typed_detailing_index", {}).get(
                "raw_reference_aliases_preserved"
            )
            is True
            and row.get("typed_view_rendering", {}).get("native_colour_rows_preserved")
            is True
            and row.get("typed_view_rendering", {}).get("cache_present") is True
            and row.get("typed_view_rendering", {}).get("saved_cache_count") == 0
            and row.get("typed_view_rendering", {}).get("declared_colour_count") == 1
            and row.get("typed_view_rendering", {}).get("actual_colour_count") == 1
            and row.get("typed_view_rendering", {}).get("actual_view_object_index")
            == 136
            and len(row.get("malformed_render_cases", ())) == 30
            and all(
                case["rejected_by_typed_view_state"] and not case["result_returned"]
                for case in row["malformed_render_cases"]
            )
            and row["input_unchanged"]
            and not row["load_usage"]["missing_schemas"]
            and not row["store_usage"]["missing_schemas"]
            for row in result["cases"]
        )
    )
    payload = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    with args.output.open("x", encoding="utf-8") as target:
        target.write(payload)
    print(
        json.dumps(
            {
                "typed_view_state_passed": result["typed_view_state_passed"],
                "normal_definition_admission": [
                    row["normal_definition_admission"] for row in result["cases"]
                ],
                "raw_failures": [row.get("raw_failure") for row in result["cases"]],
                "report_sha256": digest(args.output),
                "complete_source_semantics_admitted": False,
                "heldout_acceptance": False,
            }
        )
    )
    return 0 if result["typed_view_state_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
