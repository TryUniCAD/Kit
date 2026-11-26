# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace

from PairedCaptureIntake import require, sha256
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.EmitPrismSnap import EmitPrismSnap
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.ReadPrismSnap import ReadPrismSnap
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import EmitSnapPart
from convert.Formats.Fusion.DocumentCodec.BuildBodyPart import BuildBodyPart
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.Materials.BuildMatPart import BuildMatPart
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.Formats.Fusion.DocumentCodec.PackDocument import PackDocument
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Records.EmitDesign import EmitDesign


def pack_snapshot(author, builder, owners):
    spec = author.SpecValue
    design = EmitDesign(author)
    parts = BuildBodyPart(spec, design) + BuildMatPart(design)
    initial = ReadDocument(PackDocument(design, spec.Title, parts))
    require(not initial.Snapshots, "P03 snapshot generation requires its own bare Boss design")
    snapshot = builder.build_snapshot(initial)
    # The current codec and the measured P03 control use the eight-byte prism layout.
    snapshot = replace(snapshot, Header=replace(snapshot.Header, IntWidth=8))
    wire = EmitPrismSnap(snapshot)
    require(ReadPrismSnap(wire) == snapshot, "P03 derived snapshot did not survive its typed codec")
    root_positions = tuple(range(snapshot.Header.RootCount - 1, 0, -1))
    plan = owners.SnapshotRootPlan(*root_positions)
    # The SDK does not yet know native cache addresses for this new part. The all-zero
    # addresses are an explicit research reset policy, never a native acceptance claim.
    member = owners.stage_snapshot_owners(author, plan, addresses=(0,) * len(root_positions))
    entry = DocumentSnap(member, snapshot)
    payload = PackDocument(EmitDesign(author), spec.Title, (*parts, EmitSnapPart(entry)))
    decoded = ReadDocument(payload)
    require(
        decoded.Snapshots == (entry,)
        and decoded.Bodies == initial.Bodies
        and decoded.Materials == initial.Materials
        and ReadDocument(EmitParsed(decoded)) == decoded,
        "P03 derived snapshot changed existing typed body, material or archive state",
    )
    require(owners_result(builder, decoded, entry) == root_positions, "P03 snapshot role IDs changed during readback")
    return payload


def owners_result(builder, decoded, entry):
    require(builder.check_saved_ownership(decoded) is False, "P03 snapshot unexpectedly has native address evidence")
    graph = BuildGraph(decoded)
    context = SelectExtrusion(graph)
    serializer = graph.OneClass("BRepSerializer")
    ids = ResolveField(graph, serializer, "topEntityPIDGenerator", "PassiveIdGenerator")
    roots = SeriesItems(ids.Fields["scanOrderIndex"])
    addresses = SeriesItems(ids.Fields["addressOfTopEntities"])
    tool = ResolveField(graph, context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody")
    (tool_owner,) = LinkedNodes(graph, tool, "toolbodyCaches")
    (region_owner,) = LinkedNodes(graph, graph.OneClass("SketchRegionRef"), "caches")
    require(
        entry.Name == "Breps.BlobParts/" + serializer.Fields["partName"]
        and roots == (tool_owner.Fields["cachedEntityId"], region_owner.Fields["cachedEntityId"], context.Sketch.Fields["bodyId"])
        and addresses == (0,) * len(roots)
        and ids.Fields["nextId"] == max(roots) + 1,
        "P03 snapshot is not the generated tool, profile and sketch owner attachment",
    )
    return roots


def snapshot_evidence(decoded, builder):
    (entry,) = decoded.Snapshots
    roots = owners_result(builder, decoded, entry)
    return {
        "member": entry.Name,
        "member_sha256": sha256(EmitPrismSnap(entry.Snapshot)),
        "int_width": entry.Snapshot.Header.IntWidth,
        "root_ids": dict(zip(("tool_solid", "profile_region", "sketch_sheet"), roots, strict=True)),
        "native_cache_addresses": "zero_reset_unmeasured",
    }
