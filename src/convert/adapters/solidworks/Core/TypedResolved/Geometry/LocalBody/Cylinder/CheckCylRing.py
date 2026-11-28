from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalFins import (
    CheckLocalFins,
)


# vertex free rims need both oriented fin uses and exact supporting carrier ownership
def CheckCylRing(
    NodesValue: Mapping[int, XmtNode],
    CapValue: XmtNode,
    SideLoop: XmtNode,
    EdgeValue: XmtNode,
) -> tuple[XmtNode, XmtNode]:
    CapLoop = RequireXmt(NodesValue, CapValue.Integer("loop"), 15)
    SideFin = RequireXmt(NodesValue, SideLoop.Integer("halfedge"), 17)
    CapFin = RequireXmt(NodesValue, CapLoop.Integer("halfedge"), 17)
    if (
        CapLoop.Integer("face") != CapValue.IndexValue
        or CapLoop.Integer("next")
        or EdgeValue.Integer("halfedge") != SideFin.IndexValue
    ):
        raise ValueError("local cylinder rim has a foreign loop")
    for FinValue, MateValue, LoopValue, SenseValue in (
        (SideFin, CapFin, SideLoop, "+"),
        (CapFin, SideFin, CapLoop, "-"),
    ):
        CheckLocalFins(NodesValue, FinValue)
        if (
            FinValue.Integer("forward") != FinValue.IndexValue
            or FinValue.Integer("other") != MateValue.IndexValue
            or FinValue.Integer("loop") != LoopValue.IndexValue
            or FinValue.Integer("edge") != EdgeValue.IndexValue
            or FinValue.String("sense") != SenseValue
        ):
            raise ValueError("local cylinder rim fins do not close on the same edge")
    CircleValue = RequireXmt(NodesValue, EdgeValue.Integer("curve"), 31)
    PlaneValue = RequireXmt(NodesValue, CapValue.Integer("surface"), 50)
    if (
        CircleValue.Integer("owner") != EdgeValue.IndexValue
        or PlaneValue.Integer("owner") != CapValue.IndexValue
        or not CircleValue.String("sense")
        == PlaneValue.String("sense")
        == CapValue.String("sense")
        == "+"
        or ReadXmtVector(CircleValue, "centre") != ReadXmtVector(PlaneValue, "pvec")
        or ReadXmtVector(CircleValue, "normal")
        != tuple(-Component for Component in ReadXmtVector(PlaneValue, "normal"))
        or ReadXmtVector(CircleValue, "x_axis")
        != tuple(-Component for Component in ReadXmtVector(PlaneValue, "x_axis"))
    ):
        raise ValueError("local cylinder rim has incompatible cap geometry")
    return PlaneValue, CircleValue
