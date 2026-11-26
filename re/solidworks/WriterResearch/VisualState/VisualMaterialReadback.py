# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CmgrColorReadback import ReadColorDspbr
from CmgrVisualBody import WriteCmgrVisualBody
from CmgrVisualPrefix import CmgrVisualFields
from ReadCmgrVisualPrefix import ReadCmgrVisualPrefix
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# all inline appearance owners need exact typed readback of both shader layers
def ReadVisualMaterial(
    Cursor: ArchiveCursor,
    Generation: int,
    *,
    AllowSystemTexture: bool = False,
) -> CmgrVisualFields:
    Start = Cursor.Offset
    Fields = ReadCmgrVisualPrefix(
        Cursor, Generation, AllowSystemTexture=AllowSystemTexture
    )
    ReadColorDspbr(Cursor)
    Writer = ArchiveWriter()
    WriteCmgrVisualBody(Writer, Generation, Fields, AllowSystemTexture=AllowSystemTexture)
    RequireArch(
        Writer.build(),
        Cursor.BlobValue[Start : Cursor.Offset],
        "fully typed ordinary color appearance fields",
    )
    return Fields
