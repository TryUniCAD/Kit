# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections import deque as Deque

from convert.adapters.freecad.EditShape.Sketch.WireEdge import SavedEdge
from convert.adapters.freecad.EditShape.Sketch.WireMatch import IsSameEdge, KSketchCurve
from interchange.geometry.models.Transform import Transform


# overlapping tolerance windows need a complete assignment across all saved wires
def IsEdgeMatch(
    Edges: list[SavedEdge],
    Curves: list[KSketchCurve],
    FrameValue: Transform,
    DirectedLines: bool,
) -> bool:
    Owners: dict[int, int] = {}
    Assigned: dict[int, int] = {}
    for EdgeIndex in range(len(Edges)):
        Pending = Deque([EdgeIndex])
        Parents: dict[int, int] = {}
        while Pending:
            Current = Pending.popleft()
            for CurveIndex, CurveValue in enumerate(Curves):
                if CurveIndex in Parents or not IsSameEdge(
                    Edges[Current], CurveValue, FrameValue, DirectedLines
                ):
                    continue
                Parents[CurveIndex] = Current
                if CurveIndex not in Owners:
                    break
                Pending.append(Owners[CurveIndex])
            else:
                continue
            break
        else:
            return False
        while True:
            Owner = Parents[CurveIndex]
            Owners[CurveIndex] = Owner
            Previous = Assigned.get(Owner)
            Assigned[Owner] = CurveIndex
            if Previous is None:
                break
            CurveIndex = Previous
    return len(Owners) == len(Curves)
