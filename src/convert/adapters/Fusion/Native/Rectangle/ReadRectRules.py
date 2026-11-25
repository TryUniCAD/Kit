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
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Rectangle.OrderLines import OrderLines
from convert.adapters.Fusion.Native.Rectangle.ReadRectDims import ReadRectDims
from convert.adapters.Fusion.Native.Rectangle.RectSketchProof import RectSketchProof
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from convert.adapters.Fusion.Native.Rectangle.CheckRuleFrame import CheckRuleFrame
from convert.adapters.Fusion.Native.Rectangle.ReadRectAxes import ReadRectAxes
from convert.adapters.Fusion.Native.Rectangle.ReadRectUnits import ReadRectUnits


# the selected constrained profile must prove its exact additions before sharing ordinary strict guards
def ReadRectRules(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Reverse: bool = False,
    YzDatum: bool = False,
    AllowTaper: bool = False,
) -> RectSketchProof | None:
    Geometric = Graph.ByClass("SketchGeomConstraint")
    Linear = Graph.ByClass("FusionSketchLinearDim")
    if not Geometric and not Linear:
        if (Reverse or YzDatum) and ReadRectUnits(Graph) is not UnitSystem.KMillimeter:
            raise ValueError(
                "Native unconstrained datum and reverse prisms require millimeter display units"
            )
        return None
    if len(Geometric) != 5 or len(Linear) != 2:
        raise ValueError(
            "Native constrained rectangle requires five rules and two dimensions"
        )
    DisplayUnit = ReadRectUnits(Graph)
    if Reverse and DisplayUnit is not UnitSystem.KMillimeter:
        raise ValueError("Native reverse prism requires millimeter display units")
    if YzDatum and DisplayUnit is not UnitSystem.KMillimeter:
        raise ValueError("Native YZ prism requires millimeter display units")
    Rules = LinkedNodes(Graph, Context.Sketch, "constraints")
    Dimensions = LinkedNodes(Graph, Context.Sketch, "dimensions")
    SameNodes(Rules, Geometric)
    SameNodes(Dimensions, Linear)
    Lines = OrderLines(Graph, Graph.ByClass("Line3D"))
    AnchorRule, Anchor, Origin = ReadRectAnchor(Graph, Context, Rules, Lines)
    AxisRules = ReadRectAxes(Graph, Context, Rules, AnchorRule, Lines)
    Bindings, Params, SizeRules = ReadRectDims(
        Graph, Context, Dimensions, Lines, Anchor, Reverse, YzDatum, AllowTaper
    )
    AnchorRelation = SketchRelation(
        AnchorRule.Identity,
        ConstraintKind.KCoincident,
        (ConstraintRef(Anchor.Identity), ConstraintRef(Origin.Identity)),
    )
    return RectSketchProof(
        Rules,
        Dimensions,
        Bindings,
        Params,
        Anchor,
        Origin,
        (*AxisRules, AnchorRelation, *SizeRules),
        DisplayUnit,
    )


# the free corner and the fixed origin have distinct identities and share only the proved coincidence
def ReadRectAnchor(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Rules: tuple[NativeNode, ...],
    Lines: tuple[NativeNode, ...],
) -> tuple[NativeNode, NativeNode, NativeNode]:
    Anchors = tuple(
        RuleNode for RuleNode in Rules if RuleNode.Fields["constraintType"] == 1
    )
    if len(Anchors) != 1:
        raise ValueError(
            "Native constrained rectangle requires one distinct origin coincidence"
        )
    RuleNode = Anchors[0]
    Targets = LinkedNodes(Graph, RuleNode, "geometries")
    if len(Targets) != 2 or any(
        NodeValue.ClassName != "Point3D" for NodeValue in Targets
    ):
        raise ValueError(
            "Native rectangle origin coincidence requires two point operands"
        )
    Anchor, Origin = Targets
    Endpoints = tuple(
        ResolveField(Graph, LineNode, "rStartPoint", "Point3D") for LineNode in Lines
    )
    SameNodes((*Endpoints, Origin), Graph.ByClass("Point3D"))
    if (
        Anchor not in Endpoints
        or Origin in Endpoints
        or any(
            Graph.Resolve(Point.Fields["rParent"]) != Context.Sketch
            for Point in Targets
        )
        or PointCoords(Anchor.Fields["point"]) != (0.0, 0.0, 0.0)
        or PointCoords(Origin.Fields["point"]) != (0.0, 0.0, 0.0)
    ):
        raise ValueError(
            "Native rectangle origin does not bind its distinct anchored corner"
        )
    RequireFields(Anchor, {"isOrigin": False, "isFixed": False})
    RequireFields(Origin, {"isOrigin": True, "isFixed": True})
    CheckRuleFrame(Graph, Context, RuleNode, (Origin, Anchor))
    return RuleNode, Anchor, Origin
