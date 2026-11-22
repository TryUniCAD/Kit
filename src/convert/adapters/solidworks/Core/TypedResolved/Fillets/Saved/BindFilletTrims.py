from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.Geometry.Parasolid import NativeId
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.BindFilletArc import (
    BindFilletArc,
)
from interchange.brep.Curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepEdge


# both verified cap rims must have complete and distinct native geometry ownership
def BindFilletTrims(
    NodesValue: Mapping[int, XmtNode],
    ModelValue: BrepModel,
    RadiusValue: float,
) -> BrepModel:
    NativeEdges = {
        NativeId("edge", Value.IndexValue + 1): Value
        for Value in NodesValue.values()
        if Value.KindValue == 16
    }
    Curves = {Value.id: Value for Value in ModelValue.curves}
    Points = {Value.id: Value.point for Value in ModelValue.vertices}
    BoundEdges: dict[str, BrepEdge] = {}
    BoundCurves: dict[str, CircleCurve] = {}
    for EdgeValue in ModelValue.edges:
        CurveValue = Curves[EdgeValue.curve_id]
        if isinstance(CurveValue, LineCurve):
            continue
        if not isinstance(CurveValue, CircleCurve) or CurveValue.id in BoundCurves:
            raise ValueError("saved fillet has an alternate or shared cap rim")
        KernelEdge = NativeEdges[EdgeValue.id]
        KernelCurve = RequireXmt(NodesValue, KernelEdge.Integer("curve"), 31)
        EdgeTrim, CurveTrim = BindFilletArc(
            EdgeValue, CurveValue, KernelEdge, KernelCurve, Points, RadiusValue
        )
        BoundEdges[EdgeValue.id] = EdgeTrim
        BoundCurves[CurveValue.id] = CurveTrim
    if len(BoundEdges) != 2:
        raise ValueError("saved fillet does not own two actual circular cap rims")
    return ReplaceValue(
        ModelValue,
        edges=tuple(BoundEdges.get(Value.id, Value) for Value in ModelValue.edges),
        curves=tuple(BoundCurves.get(Value.id, Value) for Value in ModelValue.curves),
    )
