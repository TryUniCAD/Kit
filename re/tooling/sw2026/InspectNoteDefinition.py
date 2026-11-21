from __future__ import annotations

import argparse
from collections import Counter
from functools import partial
import hashlib
import json
import math
from pathlib import Path
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(candidate, expected):
    path = candidate / "SourceManifest.json"
    if digest(path.read_bytes()) != expected:
        raise ValueError("frozen source manifest changed")
    manifest = json.loads(path.read_bytes())
    names = []
    for row in manifest["files"]:
        data = (candidate / "CodeRoot" / row["path"]).read_bytes()
        if len(data) != row["bytes"] or digest(data) != row["sha256"]:
            raise ValueError("frozen source differs: " + row["path"])
        names.append(row["path"])
    if len(names) != manifest["file_count"] or len(set(names)) != len(names):
        raise ValueError("source closure membership differs")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("inputs", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--inputs-sha256", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest = verify(args.candidate, args.source_sha256)
    if digest(args.inputs.read_bytes()) != args.inputs_sha256:
        raise ValueError("disclosed input custody changed")
    inputs = json.loads(args.inputs.read_bytes())
    if len(inputs["files"]) != 3 or {r["case"] for r in inputs["files"]} != {
        "ControlBeforeOpenEditSave",
        "GeneratedOpenEditSave",
        "ControlAfterOpenEditSave",
    }:
        raise ValueError("exact three disclosed derivatives are required")
    code = (args.candidate / "CodeRoot").resolve()
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
    from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef
    from convert.adapters.solidworks.Archive.Header.NativeHeader import NativeHeader
    from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
    from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Drawing.Definition.Emission.ReadDrawMut import (
        ReadDrawMut,
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
        context = BodyContext(19000, KFrontLayouts, KFrontVirtuals, KFrontSchemas)
        context.FlagsValue["owner_is_drawing"] = 1
        return context

    def store_node(writer, node):
        cls = node.ClassValue
        if (
            isinstance(cls, RuntimeClass)
            and (cls.NameValue, cls.SchemaValue) in KHeaderClasses
        ):
            WriteDrawMut(writer, node)
        else:
            WriteBodyMut(writer, node)

    typed_values = []

    def typed_identity(value):
        for index, previous in enumerate(typed_values):
            if previous is value:
                return index + 1
        if len(typed_values) >= 4096:
            raise ValueError("typed observer record identities exceed explicit bound")
        typed_values.append(value)
        return len(typed_values)

    def safe(value, depth=0):
        if depth > 24:
            raise ValueError("typed observer nesting exceeds explicit bound")
        if value is None or type(value) in (bool, int, str):
            return value
        if type(value) is float:
            return value if math.isfinite(value) else {"float_hex": value.hex()}
        if isinstance(value, ArchiveNode):
            return {
                "ref": value.IndexValue,
                "class": value.ClassValue.NameValue,
                "concrete": isinstance(value.ClassValue, RuntimeClass),
            }
        if isinstance(value, CStringValue):
            return {"cstring": value.TextValue, "unicode": value.IsUnicode}
        if type(value) is NativeHeader:
            return {
                "typed_record": "NativeHeader",
                "observer_identity": typed_identity(value),
                "self_file": safe(value.SelfFile, depth + 1),
                "model_files": safe(value.ModelFiles, depth + 1),
                "bounds": safe(value.Bounds, depth + 1),
            }
        if type(value) is NativeFileRef:
            return {
                "typed_record": "NativeFileRef",
                "observer_identity": typed_identity(value),
                "path": safe(value.PathValue, depth + 1),
                "name": safe(value.NameValue, depth + 1),
                "kind": safe(value.KindValue, depth + 1),
                "config": safe(value.ConfigValue, depth + 1),
            }
        if type(value) is bytes:
            return {"bytes": len(value), "sha256": digest(value)}
        if isinstance(value, dict):
            if len(value) > 4096:
                raise ValueError("typed observer mapping exceeds explicit bound")
            return {str(k): safe(v, depth + 1) for k, v in value.items()}
        if isinstance(value, (tuple, list)):
            if len(value) > 4096:
                raise ValueError("typed observer sequence exceeds explicit bound")
            return [safe(v, depth + 1) for v in value]
        raise TypeError(
            "unrecognized typed observer value: "
            + type(value).__module__
            + "."
            + type(value).__qualname__
        )

    def maps(snapshot, fields=False):
        result, identities = [], {}
        for item in snapshot.EntriesValue:
            value = item.EntryValue
            if isinstance(value, ArchiveNode):
                cls = value.ClassValue
                row = {
                    "slot": item.IndexValue,
                    "kind": "object",
                    "class": cls.NameValue,
                    "schema": (
                        cls.SchemaValue if isinstance(cls, RuntimeClass) else None
                    ),
                    "start": value.StartOffset,
                    "end": value.EndOffset,
                }
                if fields:
                    row["fields"] = safe(dict(value.FieldsValue))
                identities[item.IndexValue] = value
            elif isinstance(value, RuntimeClass):
                row = {
                    "slot": item.IndexValue,
                    "kind": "class",
                    "class": value.NameValue,
                    "schema": value.SchemaValue,
                }
            elif isinstance(value, ExternalClass):
                row = {
                    "slot": item.IndexValue,
                    "kind": "external",
                    "class": value.NameValue,
                }
            else:
                raise TypeError("unrecognized map entry: " + type(value).__qualname__)
            result.append(row)
        result.sort(key=lambda r: r["slot"])
        return {"counter": snapshot.CounterValue, "entries": result}, identities

    result = {
        "schema": "drawing-note-definition-grammar-observer-v1",
        "source_manifest_sha256": args.source_sha256,
        "input_manifest_sha256": args.inputs_sha256,
        "source_files": manifest["file_count"],
        "runner_sha256": digest(Path(__file__).read_bytes()),
        "scope": "exact three disclosed annotation derivatives; raw typed grammar and unchanged semantic read",
        "native_execution": False,
        "vm_execution": False,
        "normal_guards_changed": False,
        "native_acceptance": False,
        "public_writer_admission": False,
        "heldout_access": False,
        "cases": [],
    }
    for entry in inputs["files"]:
        source = Path(entry["path"])
        original = source.read_bytes()
        if len(original) != entry["bytes"] or digest(original) != entry["sha256"]:
            raise ValueError("disclosed derivative bytes differ: " + entry["case"])
        data = SldprtArchive.from_bytes(original).require("Contents/Definition")
        if (
            digest(data) != entry["definition_sha256"]
            or len(data) != entry["definition_bytes"]
        ):
            raise ValueError("disclosed Definition differs: " + entry["case"])
        row = {
            "case": entry["case"],
            "input_sha256": entry["sha256"],
            "definition_sha256": digest(data),
            "definition_bytes": len(data),
            "raw_load_complete": False,
            "raw_store_complete": False,
            "raw_byte_round_trip": False,
            "map_slots_equal": False,
            "same_object_identities": False,
            "normal_semantic_admission": False,
        }
        try:
            ReadNamedDef(data, 19000, entry["orientation"])
        except Exception as error:
            row["normal_rejection"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
        else:
            row["normal_semantic_admission"] = True
        context = new_context()
        cursor = BinaryReader(data)
        reader = GraphReader(cursor, ArchiveMaps(1), partial(ReadDrawMut, context))
        document = ArchiveNode(RuntimeClass("uiDrawingDoc_c", 1), {})
        phase = "raw_prefix"
        try:
            frame = ReadFrame(
                context,
                reader,
                FieldScope(document.FieldsValue),
                document,
                ReadSchemaMut,
                ReadFieldsMut,
            )
            ReadFieldsMut(frame, KDefPrefixFields)
            clsid = cursor.TakeBytes(len(KDrawClsid))
            if clsid != KDrawClsid:
                raise ValueError("drawing clsid differs")
            document.FieldsValue.update(
                clsid_a=int.from_bytes(clsid[:4], "little"),
                clsid_b=int.from_bytes(clsid[4:6], "little"),
                clsid_c=int.from_bytes(clsid[6:8], "little"),
                clsid_d=clsid[8:],
            )
            phase = "raw_body"
            ReadBodyMut(context, reader, document)
            if cursor.GetRemaining() != 0:
                raise ValueError("typed Definition has unread tail")
            row["raw_load_complete"] = True
            context.UsageValue.IsComplete = True
            phase = "runtime_owner_binding"
            BindFrontMut(document)
            load_map, load_ids = maps(reader.MapValue.Snapshot())
            phase = "raw_store"
            store_context = new_context()
            writer = BodyWriter(ArchiveMaps(1), store_context, store_node)
            frame = WriteFrame(
                writer,
                FieldScope(document.FieldsValue),
                document,
                WriteSchemaMut,
                WriteFieldsMut,
            )
            WriteFieldsMut(frame, KDefPrefixFields)
            writer.OutputValue.extend(KDrawClsid)
            WriteBodyMut(writer, document)
            row["raw_store_complete"] = True
            output = bytes(writer.OutputValue)
            save_map, save_ids = maps(writer.MapValue.Snapshot())
            row["output_sha256"] = digest(output)
            row["output_bytes"] = len(output)
            row["raw_byte_round_trip"] = output == data

            def wire_slots(value):
                return {
                    "counter": value["counter"],
                    "entries": [
                        {k: v for k, v in r.items() if k not in ("start", "end")}
                        for r in value["entries"]
                    ],
                }

            row["map_slots_equal"] = wire_slots(load_map) == wire_slots(save_map)
            row["same_object_identities"] = load_ids.keys() == save_ids.keys() and all(
                load_ids[k] is save_ids[k] for k in load_ids
            )
            if output != data:
                row["first_mismatch"] = next(
                    (n for n, (a, b) in enumerate(zip(data, output)) if a != b),
                    min(len(data), len(output)),
                )
            row["store_usage"] = dict(GetBodyReport(store_context.UsageValue))
        except Exception as error:
            row["raw_failure"] = {
                "phase": phase,
                "type": type(error).__name__,
                "message": str(error),
            }
        snapshot = reader.MapValue.Snapshot()
        row["map"], objects = maps(snapshot, fields=True)
        row["class_counts"] = dict(
            sorted(Counter(n.ClassValue.NameValue for n in objects.values()).items())
        )
        row["load_usage"] = dict(GetBodyReport(context.UsageValue))
        row["cursor_offset"] = cursor.GetOffset()
        row["unread_bytes"] = cursor.GetRemaining()
        row["input_unchanged"] = digest(source.read_bytes()) == entry["sha256"]
        row["raw_only_passed"] = all(
            row[k]
            for k in (
                "raw_load_complete",
                "raw_store_complete",
                "raw_byte_round_trip",
                "map_slots_equal",
                "same_object_identities",
                "input_unchanged",
            )
        )
        result["cases"].append(row)
    verify(args.candidate, args.source_sha256)
    if digest(args.inputs.read_bytes()) != args.inputs_sha256:
        raise ValueError("input custody changed during observation")
    result["data_collected"] = len(result["cases"]) == 3 and all(
        r["input_unchanged"] for r in result["cases"]
    )
    result["all_raw_round_trips"] = all(r["raw_only_passed"] for r in result["cases"])
    result["all_normal_admitted"] = all(
        r["normal_semantic_admission"] for r in result["cases"]
    )
    result["source_immutable"] = True
    with args.output.open("x", encoding="utf-8") as out:
        out.write(
            json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        )
    print(
        json.dumps(
            {
                "data_collected": result["data_collected"],
                "all_raw_round_trips": result["all_raw_round_trips"],
                "all_normal_admitted": result["all_normal_admitted"],
                "raw_failures": [r.get("raw_failure") for r in result["cases"]],
                "result_sha256": digest(args.output.read_bytes()),
                "native_acceptance": False,
            }
        )
    )
    return 0 if result["data_collected"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
