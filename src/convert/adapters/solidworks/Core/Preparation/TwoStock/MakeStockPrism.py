from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# the analytic check uses the same modeled frame and lengths as the archive composer
def MakeStockPrism(StockValue: ThroughStock) -> PrismPlan:
    FrameValue = PrincipalFrame(StockValue.AxisValue)
    Corners = tuple(
        PlaneVector(XValue * 1000.0, YValue * 1000.0)
        for XValue, YValue in StockValue.VerticesValue
    )
    return PrismPlan(
        Transform(
            SpaceVector(*FrameValue.OriginValue),
            SpaceVector(*FrameValue.AxisU),
            SpaceVector(*FrameValue.AxisV),
            SpaceVector(*FrameValue.NormalValue),
        ),
        tuple(
            LineGeometry(StartValue, EndValue)
            for StartValue, EndValue in zip(
                Corners, (*Corners[1:], Corners[0]), strict=True
            )
        ),
        StockValue.DepthValue * 1000.0,
        {},
    )
