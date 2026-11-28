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
        description="Measure actual profile display aliases through complete Definition read and store with explicit unprojected native state"
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

    from convert.adapters.solidworks.Drawing.Definition.Profiles.ReadAllProfiles import (
        ReadAllProfiles,
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

    def inspect_profiles(document):
        groups = ReadAllProfiles(document, 19000)
        results = []
        aliases = True
        for group in groups:
            raw = group.FolderValue.FieldsValue["f8f8"]
            rows = []
            for index, item in enumerate(group.ItemsValue):
                fields = item.DisplayValue.FieldsValue
                same = (
                    item.FolderValue is group.FolderValue
                    and item.DisplayValue is raw["items"][index]["o"]
                    and fields["f30"] is item.FolderValue
                    and fields["f40"] is item.ViewValue
                    and fields["f48"] is item.ReferenceValue
                    and item.ViewValue.FieldsValue["f630"] is group.FolderValue
                )
                aliases = aliases and same
                rows.append(
                    {
                        "display_object_index": item.DisplayValue.IndexValue,
                        "display_class": item.DisplayValue.ClassValue.NameValue,
                        "display_schema": item.DisplayValue.ClassValue.SchemaValue,
                        "actual_view_object_index": item.ViewValue.IndexValue,
                        "reference_object_index": item.ReferenceValue.IndexValue,
                        "reference_class": item.ReferenceValue.ClassValue.NameValue,
                        "reference_schema": item.ReferenceValue.ClassValue.SchemaValue,
                        "can_hide_suppressed_sketch": item.CanHideSuppressed,
                        "native_flag_word": fields["f200"],
                        "native_integer_set_count": fields.get(
                            "n1e0", len(fields["f1e0"])
                        ),
                        "same_actual_reference_objects": same,
                        "portable_child_sketch_join_claimed": False,
                    }
                )
            results.append(
                {
                    "folder_object_index": group.FolderValue.IndexValue,
                    "declared_count": raw.get("n", len(raw["items"])),
                    "actual_rows": len(rows),
                    "rows": rows,
                    "unprojected": list(group.Unprojected),
                }
            )
        return {
            "groups": results,
            "folder_count": len(results),
            "display_count": sum(len(group["rows"]) for group in results),
            "same_actual_reference_objects": aliases,
            "portable_child_sketch_join_claimed": False,
            "source_fields_mutated": False,
        }

    def inspect_negatives(document, orientation):
        groups = [
            group for group in ReadAllProfiles(document, 19000) if group.ItemsValue
        ]
        if len(groups) != 1 or len(groups[0].ItemsValue) != 1:
            raise ValueError(
                "disclosed profile proof requires one real display collection"
            )
        group = groups[0]
        item = group.ItemsValue[0]
        folder = group.FolderValue
        display = item.DisplayValue
        original_fields = dict(display.FieldsValue)
        original_list = folder.FieldsValue["f8f8"]
        original_bucket = folder.FieldsValue["has_fd98"]
        original_notes = folder.FieldsValue["f358"]
        model = document.FieldsValue["model"]
        sheet_detail = model.FieldsValue["f1430"].FieldsValue["f390"]
        original_sheet_list = sheet_detail.FieldsValue["f8f8"]
        names = [
            "missing profile list",
            "invalid profile list",
            "unknown profile list field",
            "missing profile items",
            "invalid profile items",
            "negative profile count",
            "boolean profile count",
            "mismatched profile count",
            "invalid profile row",
            "missing display object",
            "unknown profile row field",
            "null display object",
            "external display placeholder",
            "wrong display schema",
            "wrong display class",
            "duplicate display object",
            "missing display owner",
            "foreign display owner",
            "missing display view",
            "foreign display view",
            "missing component profile",
            "external profile placeholder",
            "wrong profile schema",
            "wrong profile class",
            "missing native flag",
            "boolean native flag",
            "negative native flag",
            "unknown native flag bits",
            "missing native integer set",
            "populated native integer set",
            "mismatched integer set count",
            "boolean integer set count",
            "populated linked state",
            "boolean linked state",
            "missing linked state",
            "missing optional data field",
            "populated optional data",
            "populated first auxiliary list",
            "populated second auxiliary list",
            "malformed auxiliary list count",
            "sheet owned profile display",
            "annotation bucket still excluded",
            "notes collection still excluded",
        ]
        results = []
        for name in names:
            display.FieldsValue.clear()
            display.FieldsValue.update(original_fields)
            changed = {"n": 1, "items": [{"o": display}]}
            folder.FieldsValue["f8f8"] = changed
            row = changed["items"][0]
            fields = display.FieldsValue
            if name == "missing profile list":
                folder.FieldsValue.pop("f8f8")
            elif name == "invalid profile list":
                folder.FieldsValue["f8f8"] = None
            elif name == "unknown profile list field":
                changed["unknown"] = 0
            elif name == "missing profile items":
                changed.pop("items")
            elif name == "invalid profile items":
                changed["items"] = None
            elif name == "negative profile count":
                changed["n"] = -1
            elif name == "boolean profile count":
                changed["n"] = True
            elif name == "mismatched profile count":
                changed["n"] = 2
            elif name == "invalid profile row":
                changed["items"] = [None]
            elif name == "missing display object":
                row.pop("o")
            elif name == "unknown profile row field":
                row["unknown"] = 0
            elif name == "null display object":
                row["o"] = None
            elif name == "external display placeholder":
                row["o"] = ArchiveNode(
                    ExternalClass("moDisplayProfileFeature_c", 1), {}
                )
            elif name == "wrong display schema":
                row["o"] = ArchiveNode(RuntimeClass("moDisplayProfileFeature_c", 2), {})
            elif name == "wrong display class":
                row["o"] = ArchiveNode(RuntimeClass("moDisplayDim_c", 1), {})
            elif name == "duplicate display object":
                changed["items"].append({"o": display})
                changed["n"] = 2
            elif name == "missing display owner":
                fields.pop("f30")
            elif name == "foreign display owner":
                fields["f30"] = sheet_detail
            elif name == "missing display view":
                fields.pop("f40")
            elif name == "foreign display view":
                fields["f40"] = model
            elif name == "missing component profile":
                fields.pop("f48")
            elif name == "external profile placeholder":
                fields["f48"] = ArchiveNode(ExternalClass("moCompProfile_c", 1), {})
            elif name == "wrong profile schema":
                fields["f48"] = ArchiveNode(RuntimeClass("moCompProfile_c", 2), {})
            elif name == "wrong profile class":
                fields["f48"] = ArchiveNode(RuntimeClass("moCompRefPlane_c", 1), {})
            elif name == "missing native flag":
                fields.pop("f200")
            elif name == "boolean native flag":
                fields["f200"] = True
            elif name == "negative native flag":
                fields["f200"] = -1
            elif name == "unknown native flag bits":
                fields["f200"] = 2
            elif name == "missing native integer set":
                fields.pop("f1e0")
            elif name == "populated native integer set":
                fields.update(f1e0=[{"key": 7}], n1e0=1)
            elif name == "mismatched integer set count":
                fields["n1e0"] = 1
            elif name == "boolean integer set count":
                fields["n1e0"] = False
            elif name == "populated linked state":
                fields["linked"] = 1
            elif name == "boolean linked state":
                fields["linked"] = False
            elif name == "missing linked state":
                fields.pop("linked")
            elif name == "missing optional data field":
                fields.pop("ff8")
            elif name == "populated optional data":
                fields["ff8"] = item.ReferenceValue
            elif name == "populated first auxiliary list":
                fields["f68"] = {"n": 1, "items": [{"o": item.ReferenceValue}]}
            elif name == "populated second auxiliary list":
                fields["fb0"] = {"n": 1, "items": [{"o": item.ReferenceValue}]}
            elif name == "malformed auxiliary list count":
                fields["fb0"] = {"n": 1, "items": []}
            elif name == "sheet owned profile display":
                sheet_detail.FieldsValue["f8f8"] = changed
            elif name == "annotation bucket still excluded":
                folder.FieldsValue["has_fd98"] = 1
            elif name == "notes collection still excluded":
                folder.FieldsValue["f358"] = {"n": 1, "items": [{"o": display}]}
            try:
                output = WriteNamedDef(NamedGraph(document, 19000, orientation))
            except Exception as error:
                expected_prefix = (
                    "blank drawing Definition excludes "
                    if name
                    in (
                        "annotation bucket still excluded",
                        "notes collection still excluded",
                    )
                    else "drawing profile display"
                )
                results.append(
                    {
                        "case": name,
                        "rejected_at_expected_boundary": isinstance(
                            error, BodyUnsupported
                        )
                        and str(error).startswith(expected_prefix),
                        "exception": type(error).__name__,
                        "message": str(error),
                        "result_returned": False,
                    }
                )
            else:
                results.append(
                    {
                        "case": name,
                        "rejected_at_expected_boundary": False,
                        "result_returned": True,
                        "unexpected_output_bytes": len(output.OutputValue),
                    }
                )
            finally:
                display.FieldsValue.clear()
                display.FieldsValue.update(original_fields)
                folder.FieldsValue["f8f8"] = original_list
                folder.FieldsValue["has_fd98"] = original_bucket
                folder.FieldsValue["f358"] = original_notes
                sheet_detail.FieldsValue["f8f8"] = original_sheet_list
        return results

    def inspect_modeled(document, orientation):
        group = next(
            group for group in ReadAllProfiles(document, 19000) if group.ItemsValue
        )
        display = group.ItemsValue[0].DisplayValue
        original = display.FieldsValue["f200"]
        results = []
        for flags in (0, 1):
            try:
                display.FieldsValue["f200"] = flags
                first = WriteNamedDef(NamedGraph(document, 19000, orientation))
                loaded = ReadNamedDef(first.OutputValue, 19000, orientation)
                second = WriteNamedDef(loaded.GraphValue)
                retained = inspect_profiles(loaded.GraphValue.DocumentValue)
                occupied = [row for row in retained["groups"] if row["rows"]]
                values = [item for row in occupied for item in row["rows"]]
                results.append(
                    {
                        "authored_native_flag": flags,
                        "output_bytes": len(first.OutputValue),
                        "output_sha256": hashlib.sha256(first.OutputValue).hexdigest(),
                        "read_store_byte_identical": first.OutputValue
                        == second.OutputValue,
                        "native_flag_preserved": len(values) == 1
                        and values[0]["native_flag_word"] == flags,
                        "boolean_projection_matches_native_bit": len(values) == 1
                        and values[0]["can_hide_suppressed_sketch"] == bool(flags & 1),
                        "actual_aliases_preserved": retained[
                            "same_actual_reference_objects"
                        ],
                        "unprojected": list(loaded.Unprojected),
                        "authored_variant_not_native_measurement": True,
                    }
                )
            except Exception as error:
                results.append(
                    {
                        "authored_native_flag": flags,
                        "failure": {
                            "type": type(error).__name__,
                            "message": str(error),
                        },
                    }
                )
            finally:
                display.FieldsValue["f200"] = original
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
        "profiles": inspect_profiles(control_read.GraphValue.DocumentValue),
        "result_property_profile_groups": len(control_read.ProfileDisplays),
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
        "schema": "kit.sw2026.drawing-profile-display-process.v1",
        "reader_manifest_sha256": args.manifest_sha256,
        "access_manifest_sha256": args.access_sha256,
        "reader_source_files": manifest["file_count"],
        "runner_sha256": digest(Path(__file__)),
        "original_frozen_writer_manifest_sha256": manifest[
            "base_frozen_writer_manifest_sha256"
        ],
        "native_proof_sha256": manifest["native_proof_sha256"],
        "scope": "view-owned native profile display aliases, empty auxiliary state and known suppression flag; portable child sketch resolution remains unprojected",
        "generated_empty_index_control": control,
        "cases": [],
        "qualified_detail_collection": "view-owned f8f8 profile displays",
        "other_detail_collections_unchanged": 33,
        "annotation_bucket_guard_unchanged": True,
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
                "profiles": inspect_profiles(normal.GraphValue.DocumentValue),
                "result_property_profile_groups": len(normal.ProfileDisplays),
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
            row["typed_profile_displays"] = inspect_profiles(document)
            row["malformed_profile_cases"] = inspect_negatives(
                document, expected[source.stem][1]
            )
            row["modeled_profile_cases"] = inspect_modeled(
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
        row["prior_sheet_annotation_rejection_retained"] = (
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
    result["typed_profile_state_passed"] = (
        result["generated_control_unchanged"]
        and control["graph_fields_restored_after_variants"]
        and control["profiles"]["display_count"] == 0
        and all(
            row["raw_byte_round_trip_passed"]
            and row["raw_load_complete"]
            and row["raw_store_complete"]
            and row["normal_definition_admission"]
            and all(
                row["normal_definition_read_store"].get(name) is True
                for name in (
                    "byte_identical",
                    "map_slots_equal",
                    "same_object_identities",
                    "result_property_uses_actual_view",
                )
            )
            and row["normal_definition_read_store"]["unprojected"]
            == [
                "drawing.detailing_edges",
                "drawing.occurrence_colours",
                "drawing.profile_displays",
            ]
            and row["typed_profile_displays"]["display_count"] == 1
            and row["typed_profile_displays"]["same_actual_reference_objects"]
            and len(row["malformed_profile_cases"]) == 43
            and all(
                case["rejected_at_expected_boundary"] and not case["result_returned"]
                for case in row["malformed_profile_cases"]
            )
            and len(row["modeled_profile_cases"]) == 2
            and all(
                case.get("read_store_byte_identical")
                and case.get("native_flag_preserved")
                and case.get("boolean_projection_matches_native_bit")
                and case.get("actual_aliases_preserved")
                and case.get("unprojected")
                == [
                    "drawing.detailing_edges",
                    "drawing.occurrence_colours",
                    "drawing.profile_displays",
                ]
                for case in row["modeled_profile_cases"]
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
                "typed_profile_state_passed": result["typed_profile_state_passed"],
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
    return 0 if result["typed_profile_state_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
