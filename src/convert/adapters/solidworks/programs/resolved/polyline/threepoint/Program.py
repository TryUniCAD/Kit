from __future__ import annotations

from collections.abc import Mapping
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KFieldValue as FieldType,
)
from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    KPrimitiveFormats as PrimitiveFormats,
    ReplayResolved,
)

from .BuildBounds import BuildBounds
from .BuildDisplay import BuildDisplay
from .BuildNotes import BuildNotes
from .PadGeometry import ComputeBounds
from .PadValidation import ValidatePad

from .Registry import (  # lgtm[py/unused-import]
    FieldOwners as FieldOwners,
    ResolvedOps as ResolvedOps,
)


KPointOffsets = (6121, 6129, 6299, 6307, 6461, 6469)

KDepthOffsets = (9408, 9480, 9968, 9992)


def PadFieldMap(
    PointsMm: tuple[tuple[float, float], ...], DepthMm: float
) -> dict[int, float]:
    ValidatePad(PointsMm, DepthMm)
    PointValues = tuple(
        Coordinate for PointPair in PointsMm for Coordinate in PointPair
    )
    FieldValues = {
        OffsetPos: ValueMeters / 1000.0
        for OffsetPos, ValueMeters in zip(KPointOffsets, PointValues, strict=True)
    }
    FieldValues.update({OffsetPos: DepthMm / 1000.0 for OffsetPos in KDepthOffsets})
    Bounds = ComputeBounds(PointsMm, DepthMm)
    FieldValues.update(BuildBounds(Bounds))
    FieldValues.update(BuildDisplay(Bounds))
    FieldValues.update(BuildNotes(PointsMm, DepthMm))
    return FieldValues


def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    ExpectedLength = ResolvedOps[-1][0] + ResolvedOps[-1][1]
    return ReplayResolved(ResolvedOps, ExpectedLength, Overrides, PrimitiveFormats)
