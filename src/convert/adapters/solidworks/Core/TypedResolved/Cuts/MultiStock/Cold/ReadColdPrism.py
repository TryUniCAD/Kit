from math import isfinite as IsFinite

from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadThruStock import (
    ReadThruStock,
)
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector


# the analytic stock must come from the four actual adjacent edges and its live depth
def ReadColdPrism(
    OwnerValue: ExtrudeOwner, FrameValue: Transform, LinkValue: NativeLink
) -> PrismPlan:
    DepthValue = OwnerValue.RequireDepth().DepthValue.value_mm
    if DepthValue is None or not IsFinite(DepthValue) or DepthValue <= 0:
        raise ValueError("cold stock requires a finite active blind D1")
    LoopValue = ReadThruStock(OwnerValue.ProfileValue, LinkValue)
    EdgesValue = LoopValue.LinesValue
    PointIds = {
        Marker
        for LineValue in EdgesValue
        for Marker in (LineValue.StartValue, LineValue.EndValue)
    }
    PointsValue = {
        Marker: LoopValue.PointsValue[Marker].PositionValue for Marker in PointIds
    }
    XValues = sorted({Point[0] for Point in PointsValue.values()})
    YValues = sorted({Point[1] for Point in PointsValue.values()})
    if (
        len(EdgesValue) != 4
        or len(PointsValue) != 4
        or len(XValues) != 2
        or len(YValues) != 2
        or not all(IsFinite(Value) for Value in (*XValues, *YValues))
    ):
        raise ValueError("typed rectangle vertices do not form four finite corners")
    FirstX, LastX = XValues
    FirstY, LastY = YValues
    Corners = ((FirstX, FirstY), (LastX, FirstY), (LastX, LastY), (FirstX, LastY))
    Adjacent = tuple(zip(Corners, (*Corners[1:], Corners[0]), strict=True))
    if {
        frozenset((PointsValue[EdgeValue.StartValue], PointsValue[EdgeValue.EndValue]))
        for EdgeValue in EdgesValue
    } != {frozenset(PairValue) for PairValue in Adjacent}:
        raise ValueError("typed rectangle lines do not bind the four adjacent sides")
    return PrismPlan(
        FrameValue,
        tuple(
            LineGeometry(PlaneVector(*Start), PlaneVector(*Finish))
            for Start, Finish in Adjacent
        ),
        DepthValue,
        {},
    )
