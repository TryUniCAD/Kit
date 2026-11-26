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


# the saved tail operands and observed dependency slots encode different orders
def CheckAnchorWire(Graph: NativeGraph, SketchNode: NativeNode) -> None:
    RulesValue = LinkedNodes(Graph, SketchNode, "constraints")
    Coincidence = RulesValue[-1]
    Anchor, Origin = LinkedNodes(Graph, Coincidence, "geometries")
    assert Anchor.Identity != Origin.Identity
    assert Anchor.Fields["isFixed"] is False and Origin.Fields["isFixed"] is True
    assert Anchor.Fields["isOrigin"] is False and Origin.Fields["isOrigin"] is True
    assert (
        PointCoords(Anchor.Fields["point"])
        == PointCoords(Origin.Fields["point"])
        == (0.0, 0.0, 0.0)
    )
    assert tuple(
        (Graph.Resolve(SlotValue.Target), SlotValue.ObserverIndex)
        for SlotValue in Coincidence.Frame.Subjects or ()
    ) == ((Origin, 0), (Anchor, 0))
    Width, Height = LinkedNodes(Graph, SketchNode, "dimensions")
    WidthAnchor, WidthEnd = LinkedNodes(Graph, Width, "geometries")
    HeightEnd, HeightAnchor = LinkedNodes(Graph, Height, "geometries")
    assert WidthAnchor == HeightAnchor == Anchor
    assert PointCoords(WidthEnd.Fields["point"]) == (4.0, 0.0, 0.0)
    assert PointCoords(HeightEnd.Fields["point"]) == (0.0, 2.0, 0.0)
    Settings = Graph.OneClass("CommonDataAssetSettings")
    for Dimension, Endpoint, AnchorRank in (
        (Width, WidthEnd, 1),
        (Height, HeightEnd, 2),
    ):
        Subjects = tuple(
            (Graph.Resolve(SlotValue.Target), SlotValue.ObserverIndex)
            for SlotValue in Dimension.Frame.Subjects or ()
        )
        assert Subjects == (
            (Settings, AnchorRank - 1),
            (Anchor, AnchorRank),
            (Endpoint, 0),
        )
