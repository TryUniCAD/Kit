from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.ReadRingPoint import (
    ReadRingPoint,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)


# an ordinary full circle needs a finite centre and a representable positive seam displacement
@DataClass(frozen=True, slots=True)
class CircleInput:
    CenterValue: tuple[float, float]
    RadiusValue: float
    VersionValue: int

    # validate the complete native circle domain before allocating any sketch objects
    def __post_init__(self) -> None:
        if (
            type(CastValue(object, self.VersionValue)) is not int
            or self.VersionValue != 19000
        ):
            raise ValueError("circle construction requires archive version 19000")
        CenterValue = ReadRingPoint(self.CenterValue)
        RadValue = ReadStyleNum(self.RadiusValue, "circle radius", LowerLimit=0)
        MarkerValue = ReadRingPoint((CenterValue[0] + RadValue, CenterValue[1]))
        if MarkerValue == CenterValue:
            raise ValueError("circle seam must be distinct from its centre")
        object.__setattr__(self, "CenterValue", CenterValue)
        object.__setattr__(self, "RadiusValue", RadValue)

    # the ordinary positive orientation is constructed with its seam on the positive sketch x axis
    @property
    def MarkerValue(self) -> tuple[float, float]:
        return (self.CenterValue[0] + self.RadiusValue, self.CenterValue[1])
