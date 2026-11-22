from collections.abc import Mapping
from dataclasses import replace as ReplaceValue
from math import isclose as IsClose, pi as PiValue

from convert.Geometry.Parasolid import ConicCurveRange, NativeId
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Topology.BrepTopology import BrepEdge
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.VectorSpace import SpaceVector


# the actual negative curve sense reverses the parameter frame while retaining the directed edge endpoints
def BindFilletArc(
    EdgeValue: BrepEdge,
    CurveValue: CircleCurve,
    KernelEdge: XmtNode,
    KernelCurve: XmtNode,
    Points: Mapping[str, SpaceVector],
    RadiusValue: float,
) -> tuple[BrepEdge, CircleCurve]:
    Sense = KernelCurve.String("sense")
    NativeAxis = ReadXmtVector(KernelCurve, "normal")
    AxisValue = CurveValue.axis
    if (
        Sense not in ("+", "-")
        or KernelCurve.Integer("owner") != KernelEdge.IndexValue
        or KernelEdge.Integer("curve") != KernelCurve.IndexValue
        or CurveValue.id != NativeId("curve", KernelCurve.IndexValue + 1)
        or KernelCurve.FieldsValue.get("radius") != RadiusValue
        or (AxisValue.x, AxisValue.y, AxisValue.z) != NativeAxis
    ):
        raise ValueError(
            "saved fillet circular rim is foreign to the native edge or carrier"
        )
    Curve = ReplaceValue(
        CurveValue,
        axis=(
            AxisValue
            if Sense == "+"
            else SpaceVector(-AxisValue.x, -AxisValue.y, -AxisValue.z)
        ),
        attributes=FreezeMapping(
            {**CurveValue.attributes, "parasolid.curve_sense": Sense}
        ),
    )
    Start, Final = ConicCurveRange(
        Curve, Points[EdgeValue.start_vertex_id], Points[EdgeValue.end_vertex_id]
    )
    if not IsClose(Final - Start, PiValue / 2, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(
            "saved fillet curved trim does not trace the actual quarter round"
        )
    return ReplaceValue(EdgeValue, start_parameter=Start, end_parameter=Final), Curve
