# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Rectangle.ReadRectEdges import ReadRectEdges


# the complete connected first boss dependency graph must follow the verified scoped sketch drivers
def CheckRectDeps(
    Graph: NativeGraph, Context: ExtrudeContext, SketchBindings: tuple[NativeNode, ...]
) -> None:
    Matrix = ResolveField(
        Graph, Context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    (PlaneRef,) = LinkedNodes(Graph, Matrix, "dataRefs")
    (Profile,) = LinkedNodes(Graph, Context.Extrude, "profileDataRefs")
    (Region,) = LinkedNodes(Graph, Profile, "dataRefs")
    ToolNode = ResolveField(
        Graph, Context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    Component = Graph.OneClass("DcComponent").ObjectId
    Sketch, BossId = Context.SketchFeature.ObjectId, Context.Extrude.ObjectId
    Plane, Place = PlaneRef.ObjectId, Matrix.ObjectId
    Width, Height = (NodeValue.ObjectId for NodeValue in SketchBindings)
    RegionId, ProfileId, ToolId = Region.ObjectId, Profile.ObjectId, ToolNode.ObjectId
    Along, Taper = Context.Along.ObjectId, Context.Taper.ObjectId
    Order = (
        Component,
        Plane,
        Place,
        Width,
        Height,
        Sketch,
        RegionId,
        ProfileId,
        Along,
        Taper,
        ToolId,
        BossId,
    )
    Edges = {
        (Component, Sketch, 4096),
        (Component, BossId, 4096),
        (Plane, Place, 1),
        (Place, Sketch, 1),
        (Width, Sketch, 1),
        (Height, Sketch, 1),
        (Sketch, RegionId, 4),
        (RegionId, ProfileId, 1),
        (ProfileId, ToolId, 1),
        (Along, ToolId, 1),
        (Taper, ToolId, 1),
        (ToolId, BossId, 1),
    }
    Compute = ResolveField(
        Graph, Context.Fragment, "rComputeManager", "DcComputeManager"
    )
    Dependencies = ResolveField(
        Graph, Context.Fragment, "rDependencyManager", "DcDependencyManager"
    )
    RequireFields(Compute, {"sortIsCurrent": True})
    RequireFields(Dependencies, {"mapsAreCurrent": True})
    if (
        tuple(
            NodeValue.ObjectId
            for NodeValue in LinkedNodes(Graph, Compute, "sortedNodesAll")
        )
        != Order
        or ReadRectEdges(Graph, Dependencies.Fields["successorMap"]) != Edges
        or ReadRectEdges(Graph, Dependencies.Fields["predecessorMap"])
        != {(Second, First, KindValue) for First, Second, KindValue in Edges}
    ):
        raise ValueError(
            "Native rectangle compute order or reciprocal dependencies disagree"
        )
    SameNodes(
        LinkedNodes(Graph, Context.SketchFeature, "childNodes"),
        (PlaneRef, Matrix, *SketchBindings),
    )
