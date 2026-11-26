# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.ContourSurf import (
    ProfileOwner,
    ReadContourEdge,
    ReadTrimSurface,
)
from convert.adapters.solidworks.Resolved.ContourTrim import ReadRectEnd
from convert.adapters.solidworks.Sketch.CircularRecords import (
    CircularHeader,
    CircularMember,
)


# an empty body configuration must still prove that its cached trim owns the circle
def ReadOnlyTail(
    Cursor: ArchiveCursor, Profile: CircularHeader, Circle: CircularMember
) -> int:
    RequireArch(Cursor.ReadInts("<2H"), (0, 4), "standalone circular profile flags")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<2i"), (-1, 0), "standalone circular profile state")
    (StateWord,) = Cursor.ReadInts("<I")
    RequireArch(Cursor.ReadInts("<H"), (0,), "standalone profile has no body contour")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<H"), (1,), "one cached circular trim surface")
    Owner: ProfileOwner = {
        "profile_object": Profile["feature_node"],
        "native_feature_id": Profile["feature_id"],
    }
    Surface = ReadTrimSurface(Cursor, Owner)
    RequireArch(Cursor.ReadInts("<H"), (1,), "one cached circular trim edge")
    EdgeValue = ReadContourEdge(Cursor, Owner, Surface)
    RequireArch(
        (EdgeValue["class"], EdgeValue["edge_id"]),
        ("moSegmRightTrimEdgeIdRep_c", Circle["native_id"]),
        "standalone trim selects its owned circular member",
    )
    RequireArch(Cursor.ReadInts("<i"), (0,), "standalone circular profile return")
    _ = ReadRectEnd(Cursor, False)
    return StateWord
