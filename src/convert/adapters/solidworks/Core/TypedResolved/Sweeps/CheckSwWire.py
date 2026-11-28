from collections.abc import Mapping
from math import dist as CalcDist, ulp as CalcUlp

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.geometry.Models.GeometryCurves import ArcGeometry


# the physical path owns two ordered vertices that bound the actual sketch arc
def CheckWireEnds(
    NodesValue: Mapping[int, XmtNode],
    BodyValue: XmtNode,
    EdgeValue: XmtNode,
    RadiusValue: float,
) -> None:
    FirstUse = RequireXmt(NodesValue, EdgeValue.Integer("halfedge"), 17)
    OtherUse = RequireXmt(NodesValue, FirstUse.Integer("other"), 17)
    FirstVertex = RequireXmt(NodesValue, FirstUse.Integer("vertex"), 18)
    OtherVertex = RequireXmt(NodesValue, OtherUse.Integer("vertex"), 18)
    if (
        (FirstUse.String("sense"), OtherUse.String("sense")) != ("+", "-")
        or OtherUse.Integer("other") != FirstUse.IndexValue
        or BodyValue.Integer("vertex") != FirstVertex.IndexValue
        or FirstVertex.Integer("next") != OtherVertex.IndexValue
        or OtherVertex.Integer("previous") != FirstVertex.IndexValue
        or OtherVertex.Integer("next")
        or FirstVertex.Integer("previous")
        or FirstVertex.Integer("point") != BodyValue.Integer("boundary_point")
    ):
        raise ValueError("SOLIDWORKS saved sweep path has an alternate trim order")
    for UseValue, VertexValue, ExpectedPoint in (
        (FirstUse, FirstVertex, (RadiusValue, RadiusValue, 0.0)),
        (OtherUse, OtherVertex, (0.0, 0.0, 0.0)),
    ):
        PointValue = RequireXmt(NodesValue, VertexValue.Integer("point"), 29)
        if (
            UseValue.Integer("edge") != EdgeValue.IndexValue
            or UseValue.Integer("loop")
            or UseValue.Integer("curve")
            or VertexValue.Integer("owner") != BodyValue.IndexValue
            or VertexValue.Integer("halfedge") != UseValue.IndexValue
            or PointValue.Integer("owner") != VertexValue.IndexValue
            or CalcDist(ReadXmtVector(PointValue, "pvec"), ExpectedPoint)
            > 8 * CalcUlp(RadiusValue)
        ):
            raise ValueError(
                "SOLIDWORKS saved sweep path endpoints disagree with its sketch"
            )


# selected path carrier must agree with the actual positive quarter arc and its owning edge
def CheckSwWire(
    NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode, PathValue: ArcGeometry
) -> None:
    CurveValue = RequireXmt(NodesValue, BodyValue.Integer("boundary_curve"), 31)
    EdgeValue = RequireXmt(NodesValue, CurveValue.Integer("owner"), 16)
    ShellValue = RequireXmt(NodesValue, BodyValue.Integer("shell"), 13)
    if (
        ShellValue.Integer("body") != BodyValue.IndexValue
        or ShellValue.Integer("face")
        or ShellValue.Integer("edge") != EdgeValue.IndexValue
        or EdgeValue.Integer("owner") != ShellValue.IndexValue
        or EdgeValue.Integer("curve") != CurveValue.IndexValue
        or CurveValue.Integer("next")
        or CurveValue.Integer("previous")
        or CurveValue.String("sense") != "+"
        or CurveValue.FieldsValue["radius"] != PathValue.Radius
        or ReadXmtVector(CurveValue, "centre")
        != (PathValue.Center.x, PathValue.Center.y, 0.0)
        or ReadXmtVector(CurveValue, "normal") != (0.0, 0.0, 1.0)
        or ReadXmtVector(CurveValue, "x_axis") != (1.0, 0.0, 0.0)
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep path carrier disagrees with its selected sketch"
        )
    CheckWireEnds(NodesValue, BodyValue, EdgeValue, PathValue.Radius)
