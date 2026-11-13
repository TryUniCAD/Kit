from __future__ import annotations

from collections.abc import Mapping
import math as MathLib

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    KPrimitiveFormats,
    ReplayResolved,
)
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KFieldValue as FieldType,
)
from convert.adapters.solidworks.programs.resolved.polyline.sixpoint.Program import (
    HasPolygonCross,
)

from .Registry import (  # lgtm[py/unused-import]
    KFieldOwners as KFieldOwners,
    KResolvedOps as KResolvedOps,
)


KPointOffsets = (
    6121,
    6129,
    6299,
    6307,
    6461,
    6469,
    6623,
    6631,
    6785,
    6793,
)

KDepthOffsets = (10014, 10086, 10574, 10598)


def PadFieldMap(
    PointsMm: tuple[tuple[float, float], ...], DepthMm: float
) -> dict[int, float]:
    if len(PointsMm) != 5 or any(len(PointPair) != 2 for PointPair in PointsMm):
        raise SldprtFormatError("five-line polyline requires exactly five vertices")
    PointValues = tuple(
        Coordinate for PointPair in PointsMm for Coordinate in PointPair
    )
    if not all(MathLib.isfinite(ValueItem) for ValueItem in PointValues):
        raise SldprtFormatError("five-line vertices must be finite")
    if len(set(PointsMm)) != len(PointsMm):
        raise SldprtFormatError("five-line vertices must be unique")
    if HasPolygonCross(PointsMm):
        raise SldprtFormatError("five-line edges must not intersect")
    AreaTwice = sum(
        PointsMm[IndexPos][0] * PointsMm[(IndexPos + 1) % 5][1]
        - PointsMm[(IndexPos + 1) % 5][0] * PointsMm[IndexPos][1]
        for IndexPos in range(5)
    )
    if AreaTwice == 0.0:
        raise SldprtFormatError("five-line area must be nonzero")
    if not MathLib.isfinite(DepthMm) or DepthMm <= 0.0:
        raise SldprtFormatError("five-line depth must be finite and positive")
    FieldValues = {
        OffsetPos: ValueMeters / 1000.0
        for OffsetPos, ValueMeters in zip(KPointOffsets, PointValues, strict=True)
    }
    FieldValues.update({OffsetPos: DepthMm / 1000.0 for OffsetPos in KDepthOffsets})
    return FieldValues


def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    ExpectedLength = KResolvedOps[-1][0] + KResolvedOps[-1][1]
    return ReplayResolved(KResolvedOps, ExpectedLength, Overrides, KPrimitiveFormats)
