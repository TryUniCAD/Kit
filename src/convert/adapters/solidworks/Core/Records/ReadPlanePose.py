# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose

from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPose
from convert.adapters.solidworks.Container.PlaneBasis import (
    KSavedBasis,
    KUnitRows,
    IsOrthonormal,
    MatrixAxes,
)
from convert.adapters.solidworks.Core.Records.ReadLocalOwner import ReadLocalOwner


# timestamp variability must not hide a structurally checked principal sketch attachment
def ReadPlanePose(
    DataValue: bytes,
    Offset: int,
    EndValue: int,
    OwnerValue: tuple[int, int, int],
    StartValue: int,
) -> tuple[int, int, KSavedBasis, int | None] | None:
    if not 0 <= StartValue <= Offset - 85 < Offset < EndValue <= len(DataValue):
        return None
    LocalValue = ReadLocalOwner(DataValue, Offset - 85, EndValue)
    if LocalValue != (*OwnerValue, Offset):
        return None
    Cursor = FieldCursor(DataValue, Offset - 4)
    try:
        Generation, PlaneObjectId = Cursor.ReadInts("<Ii")
        _ = Cursor.ReadInts("<I")
        if Generation not in (18000, 19000) or PlaneObjectId not in (2, 3, 4):
            return None
        RequireArch(Cursor.ReadInts("<H"), (0,), "absent plane reference child")
        (AxisCode,) = Cursor.ReadInts("<i")
        RequireArch(AxisCode, 5 - PlaneObjectId, "principal plane reference axis")
        BasisOffset = Cursor.Offset + 1
        BasisValue, ShiftScale = ReadLocalPose(Cursor)
        RequireArch(Cursor.Offset <= EndValue, True, "bounded principal plane pose")
        RequireArch(ShiftScale, (0, 0, 0, 1), "principal plane pose origin and scale")
        Directions = MatrixAxes(BasisValue if BasisValue is not None else KUnitRows)
        RequireArch(IsOrthonormal(Directions), True, "principal plane pose basis")
        RequireArch(
            Directions[2],
            tuple(1.0 if Index == AxisCode - 1 else 0.0 for Index in range(3)),
            "saved sketch normal agrees with its principal plane",
        )
        FirstAxis, SecondAxis, Normal = Directions
        RequireArch(
            all(
                IsClose(
                    FirstAxis[(Index + 1) % 3] * SecondAxis[(Index + 2) % 3]
                    - FirstAxis[(Index + 2) % 3] * SecondAxis[(Index + 1) % 3],
                    Normal[Index],
                    abs_tol=1e-9,
                )
                for Index in range(3)
            ),
            True,
            "right-handed principal sketch frame",
        )
    except ArchiveError:
        return None
    return (
        PlaneObjectId,
        AxisCode,
        Directions,
        BasisOffset if BasisValue is not None else None,
    )
