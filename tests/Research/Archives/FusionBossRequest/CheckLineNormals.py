# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Rectangle.ReadLine import ReadLine


# the directed sketch lines must carry their support normal as well as ordered geometry
def CheckLineNormal(Graph: NativeGraph, SketchNode: NativeNode) -> None:
    LinesValue = tuple(
        NodeValue
        for NodeValue in LinkedNodes(Graph, SketchNode, "children")
        if NodeValue.ClassName == "Line3D"
    )
    assert len(LinesValue) == 4
    Normal = (0.0, 0.0, 1.0)
    assert all(
        PointCoords(LineValue.Fields["planeNormal"]) == Normal
        for LineValue in LinesValue
    )
    assert len({ReadLine(Graph, LineValue, Normal) for LineValue in LinesValue}) == 4
