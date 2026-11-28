from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# the radial label position belongs to one actual neutral sketch and its own driving parameter
@DataClass(frozen=True, slots=True)
class RadialLabelIn:
    SketchId: str
    ParameterId: str
    TextPoint: tuple[float, float, float]

    # the actual sketch frame needs explicit finite tangential and normal coordinates in metres
    def __post_init__(self) -> None:
        if any(
            type(CastValue(object, IdentityValue)) is not str
            or not IdentityValue.strip()
            for IdentityValue in (self.SketchId, self.ParameterId)
        ):
            raise ValueError(
                "radial label requires actual sketch and driver identifiers"
            )
        if (
            type(CastValue(object, self.TextPoint)) is not tuple
            or len(self.TextPoint) != 3
        ):
            raise ValueError(
                "radial label requires three sketch frame coordinates in metres"
            )
        for Coordinate in self.TextPoint:
            _ = RequireScalar(Coordinate)
