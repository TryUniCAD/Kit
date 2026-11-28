from __future__ import annotations

import sys
from pathlib import Path

sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != Path(__file__).resolve().parent]

import argparse
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from uuid import UUID


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def checked_file(row):
    path = Path(row["path"])
    data = path.read_bytes()
    if len(data) != row["bytes"] or sha256(data).hexdigest() != row["sha256"]:
        raise ValueError("portable intake input custody differs: " + str(path))
    return data


def verify_source(candidate, expected):
    manifest_path = candidate / "SourceManifest.json"
    if digest(manifest_path) != expected:
        raise ValueError("portable intake SDK manifest differs")
    manifest = json.loads(manifest_path.read_bytes())
    seen = set()
    for row in manifest["files"]:
        checked_file({**row, "path": str(candidate / "CodeRoot" / row["path"])})
        seen.add(row["path"])
    if len(seen) != len(manifest["files"]) or len(seen) != manifest["file_count"]:
        raise ValueError("portable intake SDK source membership differs")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Read the exact disclosed origin drawing pairs into a bounded reversible source observation")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("pairs", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--pairs-sha256", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("portable intake output must be unused")
    manifest = verify_source(args.candidate, args.manifest_sha256)
    if digest(args.pairs) != args.pairs_sha256:
        raise ValueError("portable intake pair manifest differs")
    pairs = json.loads(args.pairs.read_bytes())
    if pairs["schema"] != "kit.sw2026.disclosed-origin-portable-pairs.v1" or len(pairs["pairs"]) != 8:
        raise ValueError("portable intake requires the four disclosed and four exact replay06 pairs")
    if sorted(row["role"] for row in pairs["pairs"]) != ["disclosed"] * 4 + ["generated-replay06"] * 4:
        raise ValueError("portable intake roles differ from the disclosed-only scope")
    code = args.candidate / "CodeRoot"
    sys.path[:0] = [str(code / "src"), str(code)]
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrInfo import ReadCmgrInfo
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import ReadSldprt
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
    from interchange.serialization.EncodeData import ToData

    node_tokens = {}
    node_objects = {}

    def identity(node):
        class_value = node.ClassValue
        node_objects.setdefault(id(node), node)
        if node_objects[id(node)] is not node:
            raise ValueError("portable intake object identity changed during its observation lifetime")
        node_tokens.setdefault(id(node), "observed-node:" + str(len(node_tokens) + 1))
        return {"class": class_value.NameValue, "schema": class_value.SchemaValue if isinstance(class_value, RuntimeClass) else None,
                "object_index": node.IndexValue, "concrete_runtime_class": isinstance(class_value, RuntimeClass), "observation_key": node_tokens[id(node)]}

    def describe(value, depth=0):
        if value is None or type(value) in (str, int, float, bool):
            return value
        if isinstance(value, ArchiveNode):
            return {"$node": identity(value)}
        if isinstance(value, CStringValue):
            return {"$cstring": value.TextValue, "unicode": value.IsUnicode}
        if isinstance(value, bytes):
            return {"$unprojected_bytes": {"bytes": len(value), "sha256": sha256(value).hexdigest()}}
        if isinstance(value, Enum):
            return {"$enum": type(value).__name__, "value": describe(value.value, depth + 1)}
        if depth >= 18:
            raise ValueError("portable intake metadata exceeds eighteen structural levels")
        if isinstance(value, Mapping):
            if any(type(key) is not str for key in value):
                raise TypeError("portable intake metadata has a nontext key")
            return {key: describe(item, depth + 1) for key, item in value.items()}
        if isinstance(value, (tuple, list, set, frozenset)) and len(value) <= 100000:
            return [describe(item, depth + 1) for item in value]
        if is_dataclass(value) and not isinstance(value, type):
            return {"$metadata_record": type(value).__name__, "fields": {item.name: describe(getattr(value, item.name), depth + 1) for item in fields(value)}}
        raise TypeError("portable intake cannot represent " + type(value).__module__ + "." + type(value).__qualname__)

    def observe_public(path, strict):
        try:
            document = ReadSldprt(path, IncludeBrep=False, IncludeTessellation=False, Strict=strict)
        except Exception as error:
            return {"read_completed": False, "exception": type(error).__name__, "diagnostic": str(error)}
        row = {"read_completed": True, "diagnostics": describe(document.diagnostics), "metadata_keys": sorted(document.metadata),
               "shape_counts": {name: len(getattr(document, name)) for name in ("configurations", "parameters", "support_planes", "sketches", "feature_timeline", "bodies", "materials")}}
        try:
            row["document_wire"] = ToData(document)
            row["wire_encoding_complete"] = True
        except Exception as error:
            row.update(wire_encoding_complete=False, wire_exception=type(error).__name__, wire_diagnostic=str(error),
                       document_metadata_observation=describe(document.metadata))
        return row

    def snapshot(roots):
        pending = list(roots)
        seen = set()
        result = []

        def nodes(value, depth=0):
            if isinstance(value, ArchiveNode):
                return [value]
            if depth > 18:
                raise ValueError("portable intake reference closure exceeds bound")
            if isinstance(value, Mapping):
                return [node for item in value.values() for node in nodes(item, depth + 1)]
            if isinstance(value, (tuple, list)) and len(value) <= 100000:
                return [node for item in value for node in nodes(item, depth + 1)]
            return []

        while pending:
            node = pending.pop(0)
            if not isinstance(node, ArchiveNode) or id(node) in seen:
                continue
            if len(seen) >= 8192:
                raise ValueError("portable intake actual graph exceeds8192 nodes")
            seen.add(id(node))
            row = {"identity": identity(node), "fields": describe(node.FieldsValue)}
            if node.ClassValue == RuntimeClass("moSketchBlockMgr_c", 1):
                raw_identity = node.FieldsValue.get("f380")
                if type(raw_identity) is bytes and len(raw_identity) == 16:
                    value = UUID(bytes_le=raw_identity)
                    row["typed_block_identity"] = {"uuid": str(value), "version": value.version, "field": "f380", "byte_order": "uuid-bytes-le"}
            result.append(row)
            pending.extend(nodes(node.FieldsValue))
        return result

    report = {"schema": "kit.sw2026.origin-portable-intake.v1", "tool_sha256": digest(Path(__file__)),
              "source_manifest_sha256": args.manifest_sha256, "source_file_count": manifest["file_count"],
              "pair_manifest_sha256": args.pairs_sha256, "cases": [], "source_immutable": True,
              "sdk_changed": False, "writer_changed": False, "vm_access": False, "native_execution": False,
              "heldout_payload_access": False, "native_acceptance": False, "heldout_acceptance": False,
              "source_semantic_admission": False, "data_collected": False}
    report["actual_node_references_retained_for_entire_case"] = True
    for pair in pairs["pairs"]:
        node_tokens.clear()
        node_objects.clear()
        drawing_data, child_data = checked_file(pair["drawing"]), checked_file(pair["child"])
        row = {"case": pair["case"], "role": pair["role"], "drawing": pair["drawing"], "child": pair["child"],
               "intake_complete": False, "public_drawing_strict": observe_public(Path(pair["drawing"]["path"]), True),
               "public_drawing_layout": observe_public(Path(pair["drawing"]["path"]), False),
               "public_child_strict": observe_public(Path(pair["child"]["path"]), True)}
        report["cases"].append(row)
        phase = "actual linked typed child"
        try:
            child_archive = SldprtArchive.from_bytes(child_data, pair["child"]["path"])
            link = ReadNativeLink(child_archive, 0)
            row["typed_child"] = {"config_complete": True, "resolved_complete": True, "configuration_info": dict(ReadCmgrInfo(child_archive.require("Contents/CMgr"), 19000)),
                                  "root": identity(link.ConfigValue.RootValue), "header": identity(link.ConfigValue.HeaderValue),
                                  "resolved_roots": [identity(value) for value in link.ResolvedValue.RootsValue],
                                  "nodes": snapshot((link.ConfigValue.RootValue, link.ConfigValue.HeaderValue, *link.ResolvedValue.RootsValue))}
            manager = ReadCmgrMut(child_archive.require("Contents/CMgr"), 19000)
            row["typed_child_manager"] = {"root": identity(manager.RootValue), "nodes": snapshot((manager.RootValue,))}
            phase = "actual typed child model Definition"
            try:
                child_definition = ReadModelDef(child_archive.require("Contents/Definition"), 19000)
                row["typed_child_definition"] = {"complete": True, "root": identity(child_definition.GraphValue.DocumentValue), "nodes": snapshot((child_definition.GraphValue.DocumentValue,))}
            except Exception as error:
                row["typed_child_definition"] = {"complete": False, "exception": type(error).__name__, "diagnostic": str(error)}
            phase = "actual child version history"
            try:
                history = ReadHistMut(child_archive.require("_MO_VERSION_19000/History"), 19000)
                row["typed_child_history"] = {"complete": True, "root": identity(history.RootValue), "nodes": snapshot((history.RootValue,))}
            except Exception as error:
                row["typed_child_history"] = {"complete": False, "exception": type(error).__name__, "diagnostic": str(error)}
            phase = "actual drawing layout orientation"
            layout = row["public_drawing_layout"]
            if not layout["read_completed"] or not layout.get("wire_encoding_complete"):
                raise ValueError("portable intake cannot select an orientation without a real public drawing layout")
            from interchange.serialization.Deserialize import FromData
            drawing_document = FromData(layout["document_wire"])
            drawing = drawing_document.DrawingValue
            if drawing is None or len(drawing.Sheets) != 1 or len(drawing.Sheets[0].Views) != 1:
                raise ValueError("portable intake requires one actual owned drawing view")
            orientation = drawing.Sheets[0].Views[0].OrientationName
            phase = "complete drawing Definition and source origin link"
            archive = SldprtArchive.from_bytes(drawing_data, pair["drawing"]["path"])
            definition = archive.require("Contents/Definition")
            named = ReadNamedDef(definition, 19000, orientation)
            row["typed_drawing"] = {"orientation": orientation, "byte_identity": WriteNamedDef(named.GraphValue).OutputValue == definition,
                                    "unprojected": list(named.Unprojected), "root": identity(named.GraphValue.DocumentValue),
                                    "nodes": snapshot((named.GraphValue.DocumentValue, ReadHeaderGraph(archive.require("Header2"), 19000)))}
            try:
                history = ReadHistMut(archive.require("_MO_VERSION_19000/History"), 19000)
                row["typed_drawing_history"] = {"complete": True, "root": identity(history.RootValue), "nodes": snapshot((history.RootValue,))}
            except Exception as error:
                row["typed_drawing_history"] = {"complete": False, "exception": type(error).__name__, "diagnostic": str(error)}
            row["intake_complete"] = row["typed_drawing"]["byte_identity"]
        except Exception as error:
            row.update(failed_phase=phase, exception=type(error).__name__, diagnostic=str(error))
        for item in (pair["drawing"], pair["child"]):
            if digest(Path(item["path"])) != item["sha256"]:
                report["source_immutable"] = False
                raise ValueError("portable intake source changed during observation")
    report["data_collected"] = report["source_immutable"] and all(row["intake_complete"] for row in report["cases"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return report["data_collected"]


if __name__ == "__main__":
    raise SystemExit(0 if main() else 3)
