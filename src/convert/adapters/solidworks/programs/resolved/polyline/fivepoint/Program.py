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

KDepthOffsets = (10012, 10084, 10572, 10596)


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
    MinimumX = min(PointPair[0] for PointPair in PointsMm)
    MaximumX = max(PointPair[0] for PointPair in PointsMm)
    MinimumY = min(PointPair[1] for PointPair in PointsMm)
    MaximumY = max(PointPair[1] for PointPair in PointsMm)
    RightmostPoint = [PointPair for PointPair in PointsMm if PointPair[0] == MaximumX]
    if len(RightmostPoint) != 1:
        raise SldprtFormatError("five-line rightmost attachment vertex must be unique")
    AttachmentX, AttachmentY = RightmostPoint[0]
    CentreX = (MinimumX + MaximumX) / 2000.0
    CentreY = (MinimumY + MaximumY) / 2000.0
    CentreZ = DepthMm / 2000.0
    HalfX = (MaximumX - MinimumX) / 2000.0
    HalfY = (MaximumY - MinimumY) / 2000.0
    HalfZ = CentreZ
    ExpandedX = HalfX * 1.1
    ExpandedY = HalfY * 1.1
    ExpandedZ = DepthMm * 0.55 / 1000.0
    Diameter = 2.0 * MathLib.sqrt(HalfX**2 + HalfY**2 + HalfZ**2)
    for OffsetPos in (8797, 9027):
        FieldValues[OffsetPos] = CentreX
    for OffsetPos in (8805, 9035):
        FieldValues[OffsetPos] = CentreY
    for OffsetPos in (8813, 9043, 4309, 4879):
        FieldValues[OffsetPos] = CentreZ
    for OffsetPos in (8821, 9051):
        FieldValues[OffsetPos] = Diameter
    for OffsetPos in (3533, 4052):
        FieldValues[OffsetPos] = CentreX - ExpandedX
    for OffsetPos in (3541, 4630):
        FieldValues[OffsetPos] = CentreY + ExpandedY
    for OffsetPos in (3680, 4246):
        FieldValues[OffsetPos] = ExpandedX
    for OffsetPos in (3688, 4254):
        FieldValues[OffsetPos] = -ExpandedX
    for OffsetPos in (3696, 4832):
        FieldValues[OffsetPos] = ExpandedY
    for OffsetPos in (3704, 4840):
        FieldValues[OffsetPos] = -ExpandedY
    for OffsetPos in (3727, 4293):
        FieldValues[OffsetPos] = CentreX
    for OffsetPos in (3735, 4871):
        FieldValues[OffsetPos] = CentreY
    FieldValues[4068] = CentreZ - ExpandedZ
    FieldValues[4638] = CentreZ + ExpandedZ
    for OffsetPos in (4262, 4816):
        FieldValues[OffsetPos] = ExpandedZ
    for OffsetPos in (4270, 4824):
        FieldValues[OffsetPos] = -ExpandedZ
    for OffsetPos in (10044, 10068):
        FieldValues[OffsetPos] = AttachmentX / 1000.0
    for OffsetPos in (10052, 10076):
        FieldValues[OffsetPos] = AttachmentY / 1000.0
    FieldValues[10241] = -AttachmentX / 1000.0
    FieldValues[10257] = -AttachmentY / 1000.0
    FieldValues[10330] = AttachmentX / 5000.0
    for OffsetPos in (10410, 10434):
        FieldValues[OffsetPos] = -DepthMm / 1000.0
    return FieldValues


def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    ExpectedLength = KResolvedOps[-1][0] + KResolvedOps[-1][1]
    return ReplayResolved(KResolvedOps, ExpectedLength, Overrides, KPrimitiveFormats)
