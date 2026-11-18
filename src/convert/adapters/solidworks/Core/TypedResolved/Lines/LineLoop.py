from collections.abc import Mapping
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDims import (
    LineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment


# qualified line rings need complete point ownership and an independently verified closed traversal
@Dataclass(frozen=True, slots=True)
class LineLoop:
    PointsValue: tuple[LinePoint, ...]
    LinesValue: tuple[LineSegment, ...]
    OrderValue: tuple[int, ...]
    OwnerValue: Mapping[str, object]
    DimsValue: LineDims | None = None
    RetiredRows: tuple[Mapping[str, object], ...] = ()
    RegionValues: tuple[Mapping[str, object], ...] = ()
