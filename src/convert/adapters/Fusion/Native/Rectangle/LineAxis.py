# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.Enums.EnumGeometry import ConstraintKind


# the line direction determines which native axis rule can constrain the saved side
def LineAxis(Graph: NativeGraph, LineNode: NativeNode) -> tuple[ConstraintKind, int]:
    Start = ResolveField(Graph, LineNode, "rStartPoint", "Point3D")
    Finish = ResolveField(Graph, LineNode, "rEndPoint", "Point3D")
    First = PointCoords(Start.Fields["point"])
    Final = PointCoords(Finish.Fields["point"])
    if First[1] == Final[1] and First[0] != Final[0]:
        return ConstraintKind.KHorizontal, 64
    if First[0] == Final[0] and First[1] != Final[1]:
        return ConstraintKind.KVertical, 128
    raise ValueError("Native rectangle axis rule refers to a nonaxis side")
