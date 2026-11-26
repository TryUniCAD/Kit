# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the
# PolyForm Strict License 1.0.0 and voids all licenses granted to you
# under it immediately and permanently.

import argparse
import json
from dataclasses import replace
from hashlib import sha256
from math import dist
from pathlib import Path

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, PointCoords, SeriesItems
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismPlane import PrismPlane
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.EmitPrismSnap import EmitPrismSnap
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import PrismSnapshot
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionEdge import RegionEdge
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import RegionFrame
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.ReadPrismSnap import ReadPrismSnap
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def build_snapshot(document):
    if len(document.Bodies) != 1 or not isinstance(document.Bodies[0].History, PrismHistory):
        raise ValueError("Snapshot probe requires one typed cuboid history")
    history = document.Bodies[0].History
    if history.Model.BasePoint != (0.0, 0.0, 0.0):
        raise ValueError("Snapshot probe requires the origin-anchored cuboid profile")
    graph = BuildGraph(document)
    selected = SelectExtrusion(graph)
    lines = tuple(node for node in LinkedNodes(graph, selected.Sketch, "children") if node.ClassName == "Line3D")
    curve_tags = {
        frozenset(PointCoords(ResolveField(graph, line, field, "Point3D").Fields["point"])
                  for field in ("rStartPoint", "rEndPoint")): CurveTag(line)
        for line in lines
    }
    if len(lines) != 4 or len(curve_tags) != 4 or len(set(curve_tags.values())) != 4:
        raise ValueError("Snapshot probe requires four distinct joined Design curves")
    if {SketchLink(tag, 0, 0, 1, 1) for tag in curve_tags.values()} != set(history.TagSet.Sketches):
        raise ValueError("Snapshot curve identities disagree with solid history")
    lower_left, lower_right, upper_left, upper_right = history.Frame.CornersCm[:4]
    corners = (upper_left, lower_left, lower_right, upper_right)
    plane = PrismPlane((upper_right[0] / 2, upper_right[1] / 2, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    edges = []
    tags = []
    for start, finish in zip(corners, (*corners[1:], corners[0]), strict=True):
        tag = curve_tags.get(frozenset((start, finish)))
        if tag is None:
            raise ValueError("Snapshot region edge has no matching Design curve")
        length = dist(start, finish)
        direction = tuple((right - left) / length for left, right in zip(start, finish, strict=True))
        edges.append(RegionEdge(0.0, length, PrismLine(start, direction, 0.0, length)))
        tags.append(SketchLink(tag, 0, 0, 1, 1))
    previous = tuple((index - 1) % len(corners) for index in range(len(corners)))
    sketch = RegionFrame(corners, tuple(edges), previous, plane, tuple(tags),
                         tuple(replace(tag, Direction=1) for tag in tags))
    profile = replace(sketch, VertexOwners=tuple(min(index, owner) for index, owner in enumerate(previous)))
    header = BrepHeader(23200, 4, 2, 10.0, 1e-6, 1e-10, 4)
    return PrismSnapshot(history.Model, history.TagSet, history.Stamp, header, history.Frame, profile, sketch)


def check_saved_ownership(document):
    graph = BuildGraph(document)
    selected = SelectExtrusion(graph)
    serializer = graph.OneClass("BRepSerializer")
    if document.Snapshots[0].Name != "Breps.BlobParts/" + serializer.Fields["partName"]:
        raise ValueError("Saved snapshot name disagrees with the Design serializer")
    generator = ResolveField(graph, serializer, "topEntityPIDGenerator", "PassiveIdGenerator")
    scan_order = SeriesItems(generator.Fields["scanOrderIndex"])
    addresses = SeriesItems(generator.Fields["addressOfTopEntities"])
    tool = ResolveField(graph, selected.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody")
    (tool_cache,) = LinkedNodes(graph, tool, "toolbodyCaches")
    (region_cache,) = tuple(node for node in LinkedNodes(graph, graph.OneClass("SketchRegionRef"), "caches")
                            if node.ClassName == "ETCachedTopology")
    expected_scope = {"assetId": document.Asset.AssetId, "scopeEntityIdentifier": selected.Component.Fields["persistentId"],
                      "scopeIdType": 2, "segmentId": 0}
    if (
        tool_cache.ClassName != "ETCachedTopology"
        or scan_order != (tool_cache.Fields["cachedEntityId"], region_cache.Fields["cachedEntityId"], selected.Sketch.Fields["bodyId"])
        or len(set(scan_order)) != 3
        or len(addresses) != 3
        or generator.Fields["nextId"] <= max(scan_order)
        or any(ObjectFields(node.Fields["scope"]) != expected_scope or node.Fields["progenitor"] is not None
               for node in (tool_cache, region_cache))
    ):
        raise ValueError("Saved snapshot roots do not resolve to their expected Design owners")
    return len(set(addresses)) == 3 and all(address > 0 for address in addresses)


def probe(path, expected_digest, saved_control):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_digest:
        raise ValueError("Snapshot probe archive digest differs")
    document = ReadDocument(raw)
    if len(document.Snapshots) != int(saved_control):
        raise ValueError("Incorrect number of input snapshots for the probe role")
    # Construct with snapshot input explicitly absent. A saved control is used only for the comparison.
    derived = build_snapshot(replace(document, Snapshots=()))
    wire = EmitPrismSnap(derived)
    if ReadPrismSnap(wire) != derived:
        raise ValueError("Snapshot codec failed an exact typed round trip")
    if saved_control and document.Snapshots[0].Snapshot != derived:
        raise ValueError("Derived snapshot and measured control have different typed state")
    return {"input_sha256": expected_digest, "role": "control" if saved_control else "constructor",
            "snapshot_bytes": len(wire), "snapshot_sha256": sha256(wire).hexdigest(),
            "region_edge_count": len(derived.Profile.Edges) + len(derived.Sketch.Edges),
            "saved_typed_state_equal": saved_control,
            "saved_owner_address_slots_distinct_nonzero": check_saved_ownership(document) if saved_control else None,
            "archive_published": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure a derived standalone cuboid snapshot without publishing an archive")
    parser.add_argument("archive", type=Path)
    parser.add_argument("sha256")
    parser.add_argument("--saved-control", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(probe(arguments.archive, arguments.sha256, arguments.saved_control), sort_keys=True))
