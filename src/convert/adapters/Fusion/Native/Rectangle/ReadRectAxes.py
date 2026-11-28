# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, RequireFields
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from convert.adapters.Fusion.Native.Rectangle.CheckRuleFrame import CheckRuleFrame
from convert.adapters.Fusion.Native.Rectangle.LineAxis import LineAxis


# every exact line needs its own matching horizontal or vertical saved rule
def ReadRectAxes(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Rules: tuple[NativeNode, ...],
    AnchorRule: NativeNode | None,
    Lines: tuple[NativeNode, ...],
) -> tuple[SketchRelation, ...]:
    ByLine: dict[str, SketchRelation] = {}
    for RuleNode in Rules:
        if RuleNode == AnchorRule:
            continue
        Targets = LinkedNodes(Graph, RuleNode, "geometries")
        if (
            len(Targets) != 1
            or Targets[0] not in Lines
            or Targets[0].Identity in ByLine
        ):
            raise ValueError(
                "Native rectangle axis rules must identify four distinct sides"
            )
        LineNode = Targets[0]
        KindValue, CodeValue = LineAxis(Graph, LineNode)
        RequireFields(RuleNode, {"constraintType": CodeValue})
        CheckRuleFrame(Graph, Context, RuleNode, (LineNode,))
        ByLine[LineNode.Identity] = SketchRelation(
            RuleNode.Identity, KindValue, (ConstraintRef(LineNode.Identity),)
        )
    if len(ByLine) != 4:
        raise ValueError(
            "Native rectangle axis rules do not cover the selected perimeter"
        )
    return tuple(ByLine.values())
