from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# privately authored sketch labels need actual neutral ownership independent of native display identity
@DataClass(frozen=True, slots=True)
class SketchLabelIn:
    SketchId: str
    ParameterId: str
    TextPoint: tuple[float, float, float]
    RouteCenter: bool

    # malformed label intent must refuse before any document projection can allocate archive objects
    def __post_init__(self) -> None:
        for Value in (self.SketchId, self.ParameterId):
            if type(CastValue(object, Value)) is not str or not Value.strip():
                raise ValueError(
                    "sketch labels require actual sketch and driver identifiers"
                )
        if (
            type(CastValue(object, self.TextPoint)) is not tuple
            or len(self.TextPoint) != 3
        ):
            raise TypeError(
                "sketch label requires three finite sketch frame coordinates"
            )
        for Coordinate in self.TextPoint:
            _ = RequireScalar(Coordinate)
        if type(CastValue(object, self.RouteCenter)) is not bool:
            raise TypeError("sketch label routing requires an explicit boolean")


# the scoped rectangle owns two independent driving labels
KSketchLabels = tuple[SketchLabelIn, SketchLabelIn]
