from dataclasses import dataclass as DataClass
from math import isclose as IsClose
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import (
    ThroughEndInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)


# the first research composition admits precisely a centered depth rectangle and one enclosed undimensioned circular through cut
@DataClass(frozen=True, slots=True)
class ThroughPartSpec:
    StockValue: ThroughStock
    CircleValue: CircleInput
    SketchName: str
    FeatureName: str
    EndValue: ThroughEndInput

    # finite geometry and exact semantic scope must be admitted before any native graph exists
    def __post_init__(self) -> None:
        if (
            type(self.StockValue) is not ThroughStock
            or type(self.CircleValue) is not CircleInput
            or type(self.EndValue) is not ThroughEndInput
        ):
            raise TypeError("through all part requires its exact typed input owners")
        StockValue = self.StockValue
        if (
            StockValue.AxisValue not in ("x", "y", "z")
            or StockValue.DepthValue <= 0
            or StockValue.DepthName != "D1"
        ):
            raise ValueError(
                "through all stock requires a principal plane and positive total mid plane depth"
            )
        LowerX = min(Point[0] for Point in StockValue.VerticesValue)
        HighX = max(Point[0] for Point in StockValue.VerticesValue)
        LowerY = min(Point[1] for Point in StockValue.VerticesValue)
        HighY = max(Point[1] for Point in StockValue.VerticesValue)
        Expected = ((LowerX, LowerY), (HighX, LowerY), (HighX, HighY), (LowerX, HighY))
        if (
            StockValue.VerticesValue != Expected
            or not IsClose(HighX - LowerX, StockValue.WidthValue)
            or not IsClose(HighY - LowerY, StockValue.HeightValue)
        ):
            raise ValueError(
                "through all stock requires its actual ordered axis aligned rectangle"
            )
        CenterX, CenterY = self.CircleValue.CenterValue
        RadiusValue = self.CircleValue.RadiusValue
        if (
            not LowerX < CenterX - RadiusValue < CenterX + RadiusValue < HighX
            or not LowerY < CenterY - RadiusValue < CenterY + RadiusValue < HighY
        ):
            raise ValueError(
                "first through all cut requires its complete circle strictly inside the stock"
            )
        NamesValue = tuple(
            ReadStyleText(NameValue, "through all feature name")
            for NameValue in (
                StockValue.SketchName,
                StockValue.FeatureName,
                self.SketchName,
                self.FeatureName,
            )
        )
        if len(set(NamesValue)) != 4:
            raise ValueError(
                "through all part requires four distinct actual feature names"
            )
