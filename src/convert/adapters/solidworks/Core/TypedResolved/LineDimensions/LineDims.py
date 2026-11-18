from collections.abc import Mapping
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxis import (
    LineAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDriver import (
    LineDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.LineOrigin import (
    LineOrigin,
)


# qualified dimension groups carry independently derived entity counts into the shared line geometry reader
@Dataclass(frozen=True, slots=True)
class LineDims:
    DriverValues: tuple[LineDriver, ...]
    AxisValues: tuple[LineAxis, ...]
    ReferencesValue: Mapping[tuple[str, int], int]
    OriginValue: LineOrigin | None = None
