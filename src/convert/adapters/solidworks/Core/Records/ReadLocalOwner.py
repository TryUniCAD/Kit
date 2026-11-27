# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KObjectRefKind,
    ArchiveError,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor


# principal references must retain their local unit and part owners before selecting geometry
def ReadLocalOwner(
    DataValue: bytes, Offset: int, EndValue: int
) -> tuple[int, int, int, int] | None:
    try:
        UnitValue = ReadTag(DataValue, Offset)
        PartValue = ReadTag(DataValue, Offset + UnitValue.size)
        RequireArch(
            (UnitValue.kind, PartValue.kind, UnitValue.wide, PartValue.wide),
            (KClassRefKind, KObjectRefKind, False, False),
            "compact local part owner references",
        )
        RequireArch(
            UnitValue.index > 0 and PartValue.index > 0, True, "allocated local owners"
        )
        Cursor = FieldCursor(DataValue, Offset + UnitValue.size + PartValue.size)
        RequireArch(Cursor.ReadInts("<B"), (0,), "absent external unit component")
        WordsValue = Cursor.ReadInts("<20I")
        RequireArch(Cursor.Offset <= EndValue, True, "bounded local part envelope")
        RequireArch(
            tuple(WordsValue[Index] for Index in (6, 14, 15, 16, 17, 18)),
            (0,) * 6,
            "absent component extras",
        )
        if WordsValue[-1] not in (18000, 19000):
            return None
    except ArchiveError:
        return None
    return WordsValue[-1], UnitValue.index, PartValue.index, Cursor.Offset
