from math import ulp

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxes import (
    PrismAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Display.DatumDisplay import (
    DatumDisplay,
)
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


# normal space vectors are measured in millimetres before checking the native metre display
def MetreVector(Value: SpaceVector) -> tuple[float, float, float]:
    return Value.x / 1000, Value.y / 1000, Value.z / 1000


# the display dimensions follow the measured half span and padding operation order
def CalcHalfSpan(
    SizesValue: tuple[float, float, float], BasisValue: tuple[float, float, float]
) -> float:
    SpanValue = sum(
        SizeValue * abs(AxisValue)
        for SizeValue, AxisValue in zip(SizesValue, BasisValue, strict=True)
    )
    return SpanValue * 0.5 + SpanValue * 0.05


# a support rectangle remains a dependent presentation of the actual analytic stock
def CalcDatumView(
    FrameValue: PlaneFrame,
    Center: tuple[float, float, float],
    SizesValue: tuple[float, float, float],
    Tolerance: float,
) -> DatumDisplay:
    Normal = FrameValue.NormalValue
    Projected = tuple(
        Position if AxisValue == 0.0 else 0.0
        for Position, AxisValue in zip(Center, Normal, strict=True)
    )
    CenterX, CenterY, CenterZ = Projected
    MarginU = CalcHalfSpan(SizesValue, FrameValue.AxisU)
    MarginV = CalcHalfSpan(SizesValue, FrameValue.AxisV)
    LabelX, LabelY, LabelZ = (
        Position + (-MarginU * AxisU + MarginV * AxisV)
        for Position, AxisU, AxisV in zip(
            Projected, FrameValue.AxisU, FrameValue.AxisV, strict=True
        )
    )
    return DatumDisplay(
        (CenterX, CenterY, CenterZ),
        (MarginU, -MarginU, MarginV, -MarginV),
        (LabelX, LabelY, LabelZ),
        Tolerance,
    )


# the finite endpoints must be the first support rectangle clipping the visible axis line
def CheckAxisViews(
    AxesValue: PrismAxes, BoundsValue: BoundingBox
) -> dict[ArchiveNode, DatumDisplay]:
    Lower, Upper = MetreVector(BoundsValue.minimum), MetreVector(BoundsValue.maximum)
    if (Lower[0], Upper[1], Lower[2]) != (0.0, 0.0, 0.0):
        raise ValueError("cache free origin axes require the signed origin box bounds")
    SizesValue = (Upper[0], -Lower[1], Upper[2])
    if min(SizesValue) <= 1e-7:
        raise ValueError("cache free origin axis stock is degenerate")
    Center = (Upper[0] * 0.5, Lower[1] * 0.5, Upper[2] * 0.5)
    Tolerance = 8 * ulp(max(SizesValue))
    Views = {
        PickValue.PlaneValue: CalcDatumView(
            PickValue.FrameValue, Center, SizesValue, Tolerance
        )
        for AxisValue in AxesValue.AxesValue
        for PickValue in AxisValue.PicksValue
    }
    for AxisIndex, AxisValue in enumerate(AxesValue.AxesValue):
        Display = Views[AxisValue.PicksValue[0].PlaneValue]
        Margin = CalcHalfSpan(
            SizesValue, ReadVector(AxisValue.DataValue.FieldsValue["f50"])
        )
        Middle = Display.CenterValue[AxisIndex]
        if not Display.IsClose(
            (AxisValue.StartValue[AxisIndex], AxisValue.EndValue[AxisIndex]),
            (Middle - Margin, Middle + Margin),
        ):
            raise ValueError(
                "cache free origin axis endpoints disagree with their finite support"
            )
    return Views
