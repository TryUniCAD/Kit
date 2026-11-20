# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CmgrVisualPrefix import CmgrVisualFields, WriteCmgrVisualPrefix
from ColorAppearance import EncodeColorDspbr
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# native explicit document colors leave the default gray shader body intact
KExplicitDspbrColor = 0xE4E4E4


# every visual owner must pair its legacy appearance with the same shader policy
def WriteCmgrVisualBody(
    Writer: ArchiveWriter,
    Generation: int,
    Fields: CmgrVisualFields,
    *,
    AllowSystemTexture: bool = False,
) -> None:
    WriteCmgrVisualPrefix(Writer, Generation, Fields, AllowSystemTexture=AllowSystemTexture)
    DspbrColor = Fields.SurfaceColor if Fields.UsesDefaultAppearance else KExplicitDspbrColor
    Writer.raw(EncodeColorDspbr(Generation, DspbrColor))
