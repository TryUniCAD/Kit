from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import sys

LOCK_SHA = "e1928c8d6ab8ad4f0944a488f789a48fea32e8b85f4215651643baf901d39e46"
SOURCE_SHA = "ced6b5c0e3ab5593c40ee776f50c68972c63b2599e49598be01d4786bffaa63d"
EDITED_SHA = "5127ba1d0360ff7e2a9137d6c2b50b3456fa91a3b2fb52fecc78ae00dedbe144"
FAULTS = (
    "active-distance",
    "second-distance",
    "second-end",
    "chooser-owner",
    "consumes-output",
    "wrapper-atom",
)


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def node_ref(value):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName

    if not isinstance(value, ArchiveNode):
        return None
    name_node = value.FieldsValue.get("f18")
    feature_id = value.FieldsValue.get("f08")
    return {
        "class": value.ClassValue.NameValue,
        "schema": value.ClassValue.SchemaValue,
        "index": value.IndexValue,
        "start_offset": value.StartOffset,
        "end_offset": value.EndOffset,
        "native_f08": feature_id if type(feature_id) is int else None,
        "name": (
            ReadNodeName(value)
            if isinstance(name_node, ArchiveNode)
            and name_node.ClassValue.NameValue == "moNodeName_c"
            else None
        ),
    }


def values(value, seen=None):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue

    seen = set() if seen is None else seen
    if isinstance(value, ArchiveNode):
        return node_ref(value)
    if isinstance(value, CStringValue):
        return value.TextValue
    if isinstance(value, dict):
        if id(value) in seen:
            return {"cycle": True}
        seen.add(id(value))
        return {str(key): values(item, seen) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [values(item, seen) for item in value]
    if isinstance(value, bytes):
        return {"bytes": len(value), "sha256": sha256(value).hexdigest()}
    require(
        value is None or type(value) in (str, bool, int, float),
        "unhandled typed archive value",
    )
    return value


def end_values(node):
    return {
        "owner": node_ref(node.FieldsValue["f818"]),
        "fields": values(dict(node.FieldsValue["f818"].FieldsValue)),
    }


def custody(case_root, state):
    require(
        case_root.name == "D01"
        and case_root.parent.name == "Disclosed"
        and case_root.parent.parent.name == "ThroughAllSourcePacket03",
        "this audit is limited to the exact disclosed Packet03 D01 subtree",
    )
    require(
        digest(case_root / "lock.json") == LOCK_SHA, "the disclosed source lock changed"
    )
    lock = json.loads((case_root / "lock.json").read_bytes())
    require(
        lock["source_locked"] is True
        and lock["heldout_source_locked"] is False
        and lock["writer_output_count"] == 0,
        "the input does not have its disclosed native source lock",
    )
    snapshot = case_root / "SavedAuthor.json"
    require(
        digest(snapshot) == lock["source_manifest_sha256"],
        "the exact native source predictions changed",
    )
    author = json.loads(snapshot.read_bytes())
    file = case_root / "Native" / state.title() / "ThroughAllD01CutForward.SLDPRT"
    expected = SOURCE_SHA if state == "source" else EDITED_SHA
    require(
        digest(file)
        == expected
        == lock["native_artifacts"][state]["sha256"]
        == author["saved_files"][state]["sha256"],
        "the immutable disclosed native save changed",
    )
    return file, author[state]


def graph(payload):
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName

    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0)
    features = {node.FieldsValue["f08"]: node for node in link.ResolvedValue.RootsValue}
    named = {ReadNodeName(node): node for node in features.values()}
    return archive, link, features, named


def mutate(payload, fault):
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt

    archive, link, _, named = graph(payload)
    boss, cut = named["StockBoss"], named["ThroughFeature"]
    end = cut.FieldsValue["f818"].FieldsValue
    if fault == "active-distance":
        end["f18"] = boss.FieldsValue["f818"].FieldsValue["f18"]
    elif fault == "second-distance":
        end["f20"] = boss.FieldsValue["f818"].FieldsValue["f18"]
    elif fault == "second-end":
        end["f10"] = 1
    elif fault == "chooser-owner":
        cut.FieldsValue["f4c0"]["f68"] = boss
    elif fault == "consumes-output":
        cut.FieldsValue["f530"] = cut.FieldsValue["f528"]
    elif fault == "wrapper-atom":
        cut.FieldsValue["f548"]["items"][0]["o"].FieldsValue["f18"] = 0
    else:
        raise ValueError("unknown diagnostic mutation")
    encoded, _ = WriteResolMut(
        link.ResolvedValue.RootsValue,
        link.ResolvedValue.ExtraFields,
        19000,
        link.ConfigValue.MapValue,
        link.ResolvedValue.ContextValue,
    )
    streams = {row.name: row.data for row in archive.records}
    streams[link.StreamName] = encoded
    return BuildSldprt(streams, FormatVersion=4)


def owners(link, named):
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import (
        ReadManagedCutAtoms,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSavedCutBodies import (
        ReadSavedCutBodies,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import (
        CheckSavedCutScope,
    )
    from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import (
        ReadDepthOwner,
    )
    from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
    from ReadThroughAllEnd import read_through_end

    boss, cut = named["StockBoss"], named["ThroughFeature"]
    end = read_through_end(cut)
    managed = ReadManagedCutAtoms(link)
    consumed, result = ReadSavedCutBodies(boss, cut, managed)
    scope = CheckSavedCutScope(link.ConfigValue.RootValue, boss, cut, consumed)
    require(
        ReadParents(boss) == (named["StockProfile"],)
        and ReadParents(cut) == (named["ThroughProfile"],),
        "the actual concept profile parent differs",
    )
    depth = ReadDepthOwner(link, boss.FieldsValue["f818"].FieldsValue["f18"])
    return (
        end,
        depth,
        {
            "consumed_atom_id": consumed,
            "result_atom_id": result,
            "scope_code": scope,
            "selection_wrapper": values(
                dict(cut.FieldsValue["f548"]["items"][0]["o"].FieldsValue)
            ),
            "selection_owner_alias": cut.FieldsValue["f4c0"]["f68"] is cut,
            "selection_component_owner_alias": cut.FieldsValue["f548"]["items"][0]["o"]
            .FieldsValue["f58"]
            .FieldsValue["owner"]
            is link.ConfigValue.RootValue,
            "managed_atoms": [
                node_ref(node)
                | {
                    "atom_id": node.FieldsValue["f140"],
                    "producer_id": node.FieldsValue["f12c"],
                }
                for node in sorted(managed, key=lambda node: node.FieldsValue["f140"])
            ],
        },
    )


def roundtrip(archive, link):
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHdrMut import (
        ReadMgrHdrMut,
    )
    from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import (
        WriteMgrHdrMut,
    )
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import (
        ReadHeaderGraph,
    )
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import (
        WriteHeadGraph,
    )
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut

    streams = {row.name: row.data for row in archive.records}
    config, saved = WriteConfigMut(
        link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue
    )
    resolved, _ = WriteResolMut(
        link.ResolvedValue.RootsValue,
        link.ResolvedValue.ExtraFields,
        19000,
        saved.MapValue,
        link.ResolvedValue.ContextValue,
    )
    manager = ReadCmgrMut(streams["Contents/CMgr"], 19000)
    header = ReadMgrHdrMut(streams["Contents/CMgrHdr2"], 19000)
    output = {
        "Contents/Config-0": config,
        link.StreamName: resolved,
        "Contents/Config-0-ModelHeader": WriteHeadGraph(
            link.ConfigValue.HeaderValue, 19000
        ),
        "Header2": WriteHeadGraph(ReadHeaderGraph(streams["Header2"], 19000), 19000),
        "Contents/CMgr": WriteCmgrMut(manager.RootValue, 19000),
        "Contents/CMgrHdr2": WriteMgrHdrMut(header.RootValue, 19000)[0],
    }
    require(
        all(output[name] == streams[name] for name in output),
        "a linked native stream changed on typed re-emission",
    )
    return {
        name: {
            "bytes": len(value),
            "sha256": sha256(value).hexdigest(),
            "byte_identity": True,
        }
        for name, value in output.items()
    }


def shape(link, features, profile):
    from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
        ReadLocalCirc,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
        ReadPrismFrame,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import (
        ReadLineLoop,
    )

    sketch = profile.FieldsValue["pd_f80"]
    fields = sketch.FieldsValue
    result = {
        "profile": node_ref(profile),
        "sketch": node_ref(sketch),
        "support": node_ref(profile.FieldsValue["pd_f78"]),
        "support_fields": values(dict(profile.FieldsValue["pd_f78"].FieldsValue)),
        "frame": values(profile.FieldsValue["pd_ff0"]),
        "counts": {name: fields[name] for name in ("npoints", "nlines", "narcs")},
        "point_rows": values(fields["points"]),
        "line_rows": values(fields["lines"]),
        "arc_rows": values(fields["arcs"]),
        "constraint_manager": values(fields["dims"]),
    }
    try:
        frame = ReadPrismFrame(profile, link.ConfigValue.RootValue, features)
        result["typed_frame"] = asdict(frame)
        result["typed_frame_admitted"] = True
    except ValueError as error:
        result.update(typed_frame_admitted=False, typed_frame_diagnostic=str(error))
    try:
        if fields["narcs"]:
            circle = ReadLocalCirc(sketch, link, True)
            require(
                circle is not None, "the circle has no complete supported typed shape"
            )
            actual, dimension = circle
            result["typed_shape"] = {
                "kind": "circle",
                "center_mm": list(actual.CenterValue),
                "radius_mm": actual.RadiusValue,
                "arc_id": actual.ArcMark,
                "center_id": actual.CenterMark,
                "driving_dimension": dimension is not None,
            }
        else:
            loop = ReadLineLoop(sketch, link)
            result["typed_shape"] = {
                "kind": "line_loop",
                "point_count": len(loop.PointsValue),
                "line_count": len(loop.LinesValue),
            }
        result["typed_shape_admitted"] = True
    except ValueError as error:
        result.update(typed_shape_admitted=False, typed_shape_diagnostic=str(error))
    return result


def public_read(file):
    from convert import open_document

    try:
        doc = open_document(
            file,
            source_format="solidworks.sldprt",
            strict=True,
            include_brep=False,
            include_tessellation=False,
        )
        return {
            "opened": True,
            "typed_status": doc.metadata.get("solidworks.typed_resolved_semantics"),
            "diagnostic_codes": [row.code for row in doc.diagnostics],
            "operations": [
                {
                    "name": row.name,
                    "kind": str(row.kind),
                    "definition": type(row.definition).__name__,
                }
                for row in doc.feature_timeline
                if row.name in ("StockBoss", "ThroughFeature")
            ],
        }
    except Exception as error:
        return {"opened": False, "error": repr(error)}


def main():
    parser = argparse.ArgumentParser(
        description="Audit only the independently locked disclosed D01 through-all source, with no CAD runtime or hidden access"
    )
    parser.add_argument("--sdk-root", required=True, type=Path)
    parser.add_argument("--case-root", required=True, type=Path)
    parser.add_argument("--state", choices=("source", "edited"), required=True)
    parser.add_argument("--fault", choices=FAULTS)
    args = parser.parse_args()
    sdk = args.sdk_root.resolve(strict=True)
    sys.path.insert(0, str(sdk / "src"))
    file, expected = custody(args.case_root.resolve(strict=True), args.state)
    original = file.read_bytes()
    payload = mutate(original, args.fault) if args.fault else original
    archive, link, features, named = graph(payload)
    if args.fault:
        try:
            owners(link, named)
        except ValueError as error:
            result = {
                "passed": True,
                "fault": args.fault,
                "rejected": True,
                "diagnostic": str(error),
            }
        else:
            raise ValueError("a diagnostic mutation entered the isolated typed grammar")
    else:
        end, depth, body = owners(link, named)
        require(
            isclose(
                depth.DepthValue.native_value,
                expected["stock"]["depth_forward_m"],
                rel_tol=1e-12,
            ),
            "the actual stock parameter does not match native readback",
        )
        require(
            expected["operation"]["dimensions"] == []
            and expected["operation"]["depth_forward_m"]
            == expected["operation"]["depth_reverse_m"]
            == 0,
            "the native through-all source acquired a distance driver",
        )
        boss, cut = named["StockBoss"], named["ThroughFeature"]
        result = {
            "passed": True,
            "archive_retention_only": True,
            "typed_stream_round_trips": roundtrip(archive, link),
            "features": [node_ref(node) for node in link.ResolvedValue.RootsValue],
            "stock": {
                "feature": node_ref(boss),
                "end": end_values(boss),
                "actual_depth_m": depth.DepthValue.native_value,
                "parameter": node_ref(depth.Parameter),
                "dimension": node_ref(depth.Dimension),
                "display": node_ref(depth.DisplayValue),
            },
            "cut": {
                "feature": node_ref(cut),
                "end": end_values(cut),
                "intent": {
                    "mode": end.ModeValue,
                    "reversed": end.IsReversed,
                    "single_ended": end.IsSingleEnded,
                    "forward_depth": end.ForwardDepth,
                    "reverse_depth": end.ReverseDepth,
                },
                "body_fields": {
                    key: values(cut.FieldsValue.get(key))
                    for key in (
                        "f810",
                        "f28",
                        "f60",
                        "f528",
                        "f530",
                        "f540",
                        "f544",
                        "f548",
                        "f4c0",
                    )
                },
            },
            "body_ownership": body,
            "stock_profile": shape(link, features, named["StockProfile"]),
            "cut_profile": shape(link, features, named["ThroughProfile"]),
            "native_measurement": {
                "body_count": expected["bodies"],
                "mass": expected["mass"],
                "prediction": expected["prediction"],
                "tree_rows": len(expected["tree"]),
            },
            "sdk_public_read": public_read(file),
            "reports": {
                key: {
                    name: report[name]
                    for name in ("completed", "missing_schemas", "provisional_schemas")
                }
                for key, report in (
                    ("config", link.ConfigValue.ReportValue),
                    ("resolved", link.ResolvedValue.ReportValue),
                )
            },
        }
    result.update(
        state=args.state,
        input_sha256=sha256(original).hexdigest(),
        diagnostic_payload_sha256=sha256(payload).hexdigest(),
        file_unchanged=digest(file) == sha256(original).hexdigest(),
        native_processes_started=0,
        hidden_inputs_read=0,
        writer_output_count=0,
    )
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
