from __future__ import annotations

import sys
from pathlib import Path, PureWindowsPath

sys.path[:] = [
    value
    for value in sys.path
    if Path(value or ".").resolve() != Path(__file__).resolve().parent
]

import argparse
from collections.abc import Mapping
import hashlib
import json


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_code(candidate, expected):
    path = candidate / "SourceManifest.json"
    if digest(path) != expected:
        raise ValueError("SDK source manifest differs")
    manifest = json.loads(path.read_bytes())
    names = set()
    for row in manifest["files"]:
        data = (candidate / "CodeRoot" / row["path"]).read_bytes()
        if (
            len(data) != row["bytes"]
            or hashlib.sha256(data).hexdigest() != row["sha256"]
        ):
            raise ValueError("SDK source bytes differ: " + row["path"])
        names.add(row["path"])
    if len(names) != len(manifest["files"]) or len(names) != manifest["file_count"]:
        raise ValueError("SDK source membership differs")
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Observe exact disclosed native profile references and their actual typed linked child"
    )
    parser.add_argument("candidate", type=Path)
    parser.add_argument("pairs", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--pairs-sha256", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("output must be unused")
    manifest = verify_code(args.candidate, args.manifest_sha256)
    if digest(args.pairs) != args.pairs_sha256:
        raise ValueError("pair custody manifest differs")
    pairs = json.loads(args.pairs.read_bytes())
    if (
        pairs["schema"] != "kit.sw2026.disclosed-profile-child-pairs.v1"
        or len(pairs["pairs"]) != 4
    ):
        raise ValueError("exactly four disclosed original/generated pairs required")
    code = args.candidate / "CodeRoot"
    sys.path[:0] = [str(code / "src"), str(code)]
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
        DatumTime,
    )
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import (
        ReadLogItems,
    )
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrInfo import ReadCmgrInfo
    from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef
    from convert.adapters.solidworks.Archive.Header.NativeHeader import NativeHeader
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import (
        ReadNamedDef,
    )
    from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import (
        WriteNamedDef,
    )

    def identity(node):
        if not isinstance(node, ArchiveNode):
            raise TypeError("expected actual archive node")
        value = node.ClassValue
        return {
            "class": value.NameValue,
            "schema": value.SchemaValue if isinstance(value, RuntimeClass) else None,
            "concrete_runtime_class": isinstance(value, RuntimeClass),
            "object_index": node.IndexValue,
        }

    def describe(value, depth=0, field_path=()):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, ArchiveNode):
            return identity(value)
        if isinstance(value, CStringValue):
            return {
                "kind": "CString",
                "text": value.TextValue,
                "is_unicode": value.IsUnicode,
            }
        if isinstance(value, NativeFileRef):
            return {
                "kind": "SDK native file metadata",
                "path": value.PathValue,
                "model_name": value.NameValue,
                "document_kind": value.KindValue,
                "configuration": value.ConfigValue,
                "wire_object_class_admission_implied": False,
            }
        if isinstance(value, NativeHeader):
            return {
                "kind": "SDK native header metadata",
                "self_file": describe(
                    value.SelfFile, depth + 1, field_path + ("SelfFile",)
                ),
                "model_files": [
                    describe(item, depth + 1, field_path + ("ModelFiles", str(index)))
                    for index, item in enumerate(value.ModelFiles)
                ],
                "bounds": describe(value.Bounds, depth + 1, field_path + ("Bounds",)),
                "wire_object_class_admission_implied": False,
            }
        if isinstance(value, bytes):
            return {
                "kind": "native bytes",
                "bytes": len(value),
                "sha256": hashlib.sha256(value).hexdigest(),
                "opaque_semantics_admitted": False,
            }
        if depth >= 6:
            raise ValueError("typed field observation exceeds six nested levels")
        if isinstance(value, Mapping):
            return {
                name: describe(item, depth + 1, field_path + (str(name),))
                for name, item in value.items()
            }
        if isinstance(value, (tuple, list)) and len(value) <= 4096:
            return [
                describe(item, depth + 1, field_path + (str(index),))
                for index, item in enumerate(value)
            ]
        raise TypeError(
            "typed observation cannot serialize "
            + type(value).__module__
            + "."
            + type(value).__qualname__
            + " at "
            + "/".join(field_path)
        )

    def text(value):
        if isinstance(value, str):
            return value
        if isinstance(value, CStringValue):
            return value.TextValue
        if isinstance(value, ArchiveNode):
            fields = value.FieldsValue
            for key in ("value", "f08"):
                if key in fields:
                    return text(fields[key])
        raise TypeError("native text has no recognized typed owner")

    def named_node(node):
        result = identity(node)
        fields = node.FieldsValue
        result["native_f08"] = describe(fields.get("f08"))
        if isinstance(fields.get("f18"), ArchiveNode):
            try:
                result["native_name"] = text(fields["f18"])
            except TypeError as error:
                result["native_name_unavailable"] = str(error)
        return result

    def references(value, depth=0):
        if isinstance(value, ArchiveNode):
            return [value]
        if depth >= 6:
            raise ValueError("reference observation exceeds six nested levels")
        if isinstance(value, Mapping):
            return [
                node for item in value.values() for node in references(item, depth + 1)
            ]
        if isinstance(value, (tuple, list)) and len(value) <= 4096:
            return [node for item in value for node in references(item, depth + 1)]
        return []

    def component_closure(roots):
        allowed = {
            "moCompProfile_c",
            "moChainComponent_c",
            "moContextChainComponent_c",
            "moReferenceChain_c",
            "moExtFeatureList_c",
            "moExtFeature_c",
            "moReferenceInternal_c",
            "moReferenceModel_c",
            "moExtObject_c",
            "moExtObjectList_c",
            "moUnitComponent_c",
            "moCStringHandle_c",
        }
        pending = list(roots)
        seen = set()
        rows = []
        while pending:
            node = pending.pop(0)
            if not isinstance(node, ArchiveNode) or id(node) in seen:
                continue
            seen.add(id(node))
            if node.ClassValue.NameValue not in allowed:
                continue
            if len(rows) >= 128:
                raise ValueError("component reference closure exceeds128 owners")
            rows.append(
                {"identity": identity(node), "fields": describe(node.FieldsValue)}
            )
            pending.extend(references(node.FieldsValue))
        return rows

    def native_path(external):
        if not isinstance(external, ArchiveNode):
            return {"available": False, "reason": "no actual external file node"}
        shared = external.FieldsValue.get("shared")
        if not isinstance(shared, Mapping):
            return {"available": False, "reason": "no typed shared file definition"}
        try:
            model_name = text(shared["h10"])
            file_path = text(shared["h18"])
        except (KeyError, TypeError) as error:
            return {
                "available": False,
                "reason": str(error),
                "shared_fields": describe(shared),
            }
        return {
            "available": True,
            "native_model_name": model_name,
            "native_file_path": file_path,
            "native_basename": PureWindowsPath(file_path).name,
            "shared_fields": describe(shared),
        }

    result = {
        "schema": "kit.sw2026.drawing-profile-child-observation.v1",
        "sdk_manifest_sha256": args.manifest_sha256,
        "pair_manifest_sha256": args.pairs_sha256,
        "native_lookup_proof_sha256": "dfceb60ee5d70e902c150ce5dec0f6496b37a0341dcb71edb478a50713e2f5a8",
        "tool_sha256": digest(Path(__file__)),
        "sdk_source_files": manifest["file_count"],
        "cases": [],
        "sdk_changed": False,
        "writer_changed": False,
        "portable_lookup_promoted": False,
        "regeneration_proven": False,
        "native_execution": False,
        "vm_access": False,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "original_heldout_verdict_changed": False,
    }
    for pair in pairs["pairs"]:
        row = {
            "case": pair["case"],
            "role": pair["role"],
            "observation_complete": False,
            "profile_lookup_promoted": False,
        }
        drawing = Path(pair["drawing"]["path"])
        child = Path(pair["child"]["path"])
        for path, expected in ((drawing, pair["drawing"]), (child, pair["child"])):
            data = path.read_bytes()
            if (
                len(data) != expected["bytes"]
                or hashlib.sha256(data).hexdigest() != expected["sha256"]
            ):
                raise ValueError("declared disclosed input differs: " + str(path))
        row["drawing_sha256"] = pair["drawing"]["sha256"]
        row["child_sha256"] = pair["child"]["sha256"]
        phase = "complete drawing Definition"
        try:
            archive = SldprtArchive.from_bytes(drawing.read_bytes(), str(drawing))
            definition = archive.require("Contents/Definition")
            loaded = ReadNamedDef(definition, 19000, pair["orientation"])
            written = WriteNamedDef(loaded.GraphValue)
            row["drawing_definition_byte_identity"] = written.OutputValue == definition
            row["drawing_unprojected"] = list(loaded.Unprojected)
            document = loaded.GraphValue.DocumentValue
            model = document.FieldsValue["model"]
            sheet = model.FieldsValue["f1430"]
            view = loaded.Rendering.ViewValue
            reference = view.FieldsValue["f5d8"]
            row["actual_view"] = identity(view)
            row["actual_view_internal_reference"] = identity(reference)
            row["view_reference_fields"] = describe(reference.FieldsValue)
            row["declared_reference_file"] = native_path(
                reference.FieldsValue.get("f3b0")
            )
            row["expected_native_resolved_path"] = pair[
                "declared_expected_native_resolved_path"
            ]
            row["actual_child_transport_path"] = str(child)
            phase = "complete actual child Header Config CMgr Resolved chain"
            child_archive = SldprtArchive.from_bytes(child.read_bytes(), str(child))
            linked = ReadNativeLink(child_archive, 0)
            row["child_config_complete"] = True
            row["child_resolved_complete"] = True
            row["child_config_usage"] = dict(linked.ConfigValue.ReportValue)
            row["child_resolved_usage"] = dict(linked.ResolvedValue.ReportValue)
            row["child_configuration_metadata"] = dict(
                ReadCmgrInfo(child_archive.require("Contents/CMgr"), 19000)
            )
            row["actual_child_model"] = named_node(linked.ConfigValue.RootValue)
            row["child_self_file"] = native_path(
                linked.ConfigValue.HeaderValue.FieldsValue.get("f38")
            )
            nodes = []
            seen = set()
            for entry in linked.ResolvedValue.MapValue.EntriesValue:
                node = entry.EntryValue
                if isinstance(node, ArchiveNode) and id(node) not in seen:
                    seen.add(id(node))
                    nodes.append(node)
            profiles = [
                node
                for node in nodes
                if node.ClassValue
                in (
                    RuntimeClass("moProfileFeature_c", 1),
                    RuntimeClass("moOriginProfileFeature_c", 1),
                )
            ]
            row["child_native_f08_owners"] = [
                named_node(node)
                for node in nodes
                if type(node.FieldsValue.get("f08")) is int
            ]
            row["child_resolved_roots"] = [
                named_node(node) for node in linked.ResolvedValue.RootsValue
            ]
            row["child_creation_logs"] = [
                {
                    "log": identity(log),
                    "native_f48": describe(log.FieldsValue.get("f48")),
                    "stamps": [
                        {
                            "stamp": identity(stamp),
                            "epoch": describe(stamp.FieldsValue.get("f18")),
                        }
                        for stamp in ReadLogItems(log, "moStamp_c")
                    ],
                }
                for log in ReadLogItems(
                    linked.ConfigValue.HeaderValue.FieldsValue.get("f20"), "moLogs_c"
                )
            ]
            row["child_profile_creation_epochs"] = [
                {
                    "profile": named_node(node),
                    "epoch": DatumTime(
                        linked.ConfigValue.HeaderValue, node.FieldsValue["f08"]
                    ),
                }
                for node in profiles
            ]
            row["child_profiles"] = [
                {"identity": named_node(node), "fields": describe(node.FieldsValue)}
                for node in profiles
            ]
            displays = []
            for group in loaded.ProfileDisplays:
                for display in group.ItemsValue:
                    wrapper = display.ReferenceValue
                    fields = wrapper.FieldsValue
                    frdata = fields.get("ff0")
                    if not isinstance(frdata, Mapping):
                        raise TypeError(
                            "selected profile reference lacks mandatory typed inline FRData"
                        )
                    feature_id = frdata.get("f00")
                    stamp = frdata.get("f08")
                    matches = [
                        node
                        for node in profiles
                        if type(feature_id) is int
                        and node.FieldsValue.get("f08") == feature_id
                    ]
                    target = matches[0] if len(matches) == 1 else None
                    lookup = {
                        "display": identity(display.DisplayValue),
                        "display_fields": describe(display.DisplayValue.FieldsValue),
                        "component_profile": identity(wrapper),
                        "wrapper_fields": describe(fields),
                        "component_reference_closure": component_closure(
                            [wrapper, reference]
                        ),
                        "native_feature_id": feature_id,
                        "native_creation_stamp": stamp,
                        "actual_child_id_match_count": len(matches),
                        "all_child_native_f08_owners_matching_frdata": [
                            named_node(node)
                            for node in nodes
                            if type(feature_id) is int
                            and type(node.FieldsValue.get("f08")) is int
                            and node.FieldsValue["f08"] == feature_id
                        ],
                        "native_f08_owner_role_not_inferred_from_scalar_match": True,
                        "profile_inheritance_rule": "native IsKindOf admits moOriginProfileFeature_c via moProfileFeature_c",
                        "actual_child_profile": (
                            named_node(target) if target is not None else None
                        ),
                        "id_selection_uses_source_names": False,
                        "portable_lookup_promoted": False,
                    }
                    if target is not None and type(feature_id) is int:
                        try:
                            epoch = DatumTime(
                                linked.ConfigValue.HeaderValue, feature_id
                            )
                            lookup["actual_child_creation_log_epoch"] = epoch
                            lookup["creation_log_epoch_equal"] = (
                                type(stamp) is int and stamp == epoch
                            )
                        except Exception as error:
                            lookup["creation_log_failure"] = {
                                "type": type(error).__name__,
                                "message": str(error),
                            }
                    displays.append(lookup)
            row["profile_displays"] = displays
            row["component_reference_closure"] = component_closure([reference])
            row["actual_sheet"] = identity(sheet)
            row["observation_complete"] = row["drawing_definition_byte_identity"]
        except Exception as error:
            row["failure"] = {
                "phase": phase,
                "type": type(error).__name__,
                "message": str(error),
            }
        row["drawing_unchanged"] = digest(drawing) == pair["drawing"]["sha256"]
        row["child_unchanged"] = digest(child) == pair["child"]["sha256"]
        result["cases"].append(row)
    _ = verify_code(args.candidate, args.manifest_sha256)
    if digest(args.pairs) != args.pairs_sha256:
        raise ValueError("pair manifest changed during observation")
    result["source_immutable"] = True
    result["data_collected"] = all(
        row["observation_complete"]
        and row["drawing_unchanged"]
        and row["child_unchanged"]
        for row in result["cases"]
    )
    with args.output.open("x", encoding="utf-8") as target:
        target.write(
            json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        )
    print(
        json.dumps(
            {
                "data_collected": result["data_collected"],
                "failures": [row.get("failure") for row in result["cases"]],
                "report_sha256": digest(args.output),
                "portable_lookup_promoted": False,
                "regeneration_proven": False,
            }
        )
    )
    return 0 if result["data_collected"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
