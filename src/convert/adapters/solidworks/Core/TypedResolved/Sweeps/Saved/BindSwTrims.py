from dataclasses import replace as ReplaceValue
from math import tau as FullTurn

from convert.Geometry.Parasolid import NativeId
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwTrim import (
    SwRimTrim,
)
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Curves.BrepPcurves import BrepPcurve, CirclePcurve, LinePcurve
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.VectorPlane import PlaneVector


# periodic native indices use the same biased identity as the shared analytic geometry decoder
def SwNativeId(KindValue: str, NodeValue: XmtNode) -> str:
    return NativeId(KindValue, NodeValue.IndexValue + 1)


# parameter curves attach to their actual reciprocal spatial uses and measured native face charts
def ReadSwCurves(ModelValue: BrepModel, TrimValue: SwRimTrim) -> dict[str, BrepPcurve]:
    RimValue = TrimValue.RimValue
    EdgeId = SwNativeId("edge", RimValue.EdgeValue)
    CircleId = SwNativeId("curve", RimValue.CircleValue)
    (EdgeValue,) = (Value for Value in ModelValue.edges if Value.id == EdgeId)
    (CircleValue,) = (Value for Value in ModelValue.curves if Value.id == CircleId)
    if (
        EdgeValue.curve_id != CircleId
        or EdgeValue.start_vertex_id != EdgeValue.end_vertex_id
        or (EdgeValue.start_parameter, EdgeValue.end_parameter) != (0.0, FullTurn)
        or type(CircleValue) is not CircleCurve
    ):
        raise ValueError("SOLIDWORKS saved sweep has a foreign portable rim edge")
    CapId = SwNativeId("coedge", RimValue.CapFin)
    WallId = SwNativeId("coedge", RimValue.WallFin)
    UseValues = {Value.id: Value for Value in ModelValue.coedges}
    for UseId, FinValue in ((CapId, RimValue.CapFin), (WallId, RimValue.WallFin)):
        UseValue = UseValues[UseId]
        if UseValue.edge_id != EdgeId or UseValue.reversed != (
            FinValue.String("sense") == "-"
        ):
            raise ValueError(
                "SOLIDWORKS saved sweep analytic use differs from its physical fin"
            )
    return {
        CapId: CirclePcurve(CapId + ":uv", PlaneVector(0.0, 0.0), CircleValue.radius),
        WallId: LinePcurve(
            WallId + ":uv",
            PlaneVector(TrimValue.StationValue, TrimValue.PhaseValue),
            PlaneVector(0.0, TrimValue.Direction),
        ),
    }


# the shared analytic model becomes a complete portable trim without a guessed spatial seam
def BindSwTrims(
    ModelValue: BrepModel, FirstTrim: SwRimTrim, SecondTrim: SwRimTrim
) -> BrepModel:
    CurvesValue = ReadSwCurves(ModelValue, FirstTrim) | ReadSwCurves(
        ModelValue, SecondTrim
    )
    if len(CurvesValue) != 4 or set(CurvesValue) != {
        Value.id for Value in ModelValue.coedges
    }:
        raise ValueError("SOLIDWORKS saved sweep has foreign portable trim uses")
    return ReplaceValue(
        ModelValue,
        coedges=tuple(
            ReplaceValue(Value, pcurve_id=CurvesValue[Value.id].id)
            for Value in ModelValue.coedges
        ),
        pcurves=tuple(CurvesValue.values()),
        vertices=tuple(
            ReplaceValue(
                Value, attributes=dict(Value.attributes) | {"periodic_seam": True}
            )
            for Value in ModelValue.vertices
        ),
    )
