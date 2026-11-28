# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, RequireFields
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from convert.adapters.Fusion.Native.Rectangle.CheckDimCache import CheckDimCache
from convert.adapters.Fusion.Native.Rectangle.CheckDimFrame import CheckDimFrame


# native dimension operands must measure the proper anchored side in their original direction
def ReadRectDim(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Dimension: NativeNode,
    Binding: NativeNode,
    Param: NativeNode,
    Lines: tuple[NativeNode, ...],
    Anchor: NativeNode,
    KindValue: ConstraintKind,
    YzDatum: bool = False,
    Fixed: bool = False,
) -> SketchRelation:
    IsWidth = KindValue is ConstraintKind.KDistanceX
    AxisValue = int(IsWidth) if YzDatum else int(not IsWidth)
    RequireFields(
        Dimension,
        {
            "constraintType": 1 << (22 + AxisValue),
            "ParentNode": LocalRef(Context.Sketch.ObjectId),
            "rParent": LocalRef(Context.Sketch.ObjectId),
            "dcParameter": LocalRef(Binding.ObjectId),
            "isSick": False,
            "isVisible": False,
            "rClientObject": None,
        },
    )
    Nodes = LinkedNodes(Graph, Dimension, "geometries")
    Matches = tuple(
        LineNode
        for LineNode in Lines
        if (
            Graph.Resolve(LineNode.Fields["rStartPoint"]),
            Graph.Resolve(LineNode.Fields["rEndPoint"]),
        )
        == Nodes
    )
    if len(Nodes) != 2 or len(Matches) != 1 or Nodes[int(not IsWidth)] != Anchor:
        raise ValueError(
            "Native rectangle dimension does not measure its exact ordered anchored side"
        )
    Points = tuple(PointCoords(NodeValue.Fields["point"]) for NodeValue in Nodes)
    CheckDimCache(Dimension.Fields, Param, Points, IsWidth, YzDatum, Fixed)
    CheckDimFrame(Graph, Dimension, Nodes, Anchor, IsWidth, Fixed)
    return SketchRelation(
        Dimension.Identity,
        ConstraintKind.KDistanceY if AxisValue else ConstraintKind.KDistanceX,
        tuple(ConstraintRef(NodeValue.Identity) for NodeValue in Nodes),
        parameter_id=Param.Identity,
    )
