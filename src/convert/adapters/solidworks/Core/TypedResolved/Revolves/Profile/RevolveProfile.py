from collections.abc import Mapping
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxis import (
    LineAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment


# the construction axis must remain outside the contour while retaining all native point and solver owners
@Dataclass(frozen=True, slots=True)
class RevolveProfile:
    LoopValue: LineLoop
    AxisValue: LineSegment
    AxisPoints: Mapping[int, LinePoint]
    AxisRules: tuple[LineAxis, ...]
    RegionValues: tuple[Mapping[str, object], ...]
