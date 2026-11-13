from __future__ import annotations

from collections.abc import Mapping

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KFieldValue as FieldType,
)
from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    KPrimitiveFormats,
    ReplayResolved,
)

from .BuildBounds import BuildBounds
from .BuildDisplay import BuildDisplay
from .BuildNotes import BuildNotes
from .PadGeometry import ComputeBounds
from .PadValidation import ValidatePad
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
    ExpectedLength = KResolvedOps[-1][0] + KResolvedOps[-1][1]
    return ReplayResolved(KResolvedOps, ExpectedLength, Overrides, KPrimitiveFormats)
