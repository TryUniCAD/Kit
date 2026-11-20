# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.api.ApiConvert import ConvertFile
from tests.Convert.Solidworks.Core.CircleOnly.AlterCircle import AlterCircle


# unresolved native histories must refuse conversion before replacing any existing destination
@TestMark.parametrize(
    "ModeValue", ("diameter", "support", "flags", "footer", "body", "history")
)
@TestMark.parametrize("StrictMode", (False, True))
def CheckWriteGuard(TmpPath: FilePath, ModeValue: str, StrictMode: bool) -> None:
    TargetPath = TmpPath / "Destination.json"
    _ = TargetPath.write_bytes(b"existing user destination")
    with RaisesError(ValueError):
        _ = ConvertFile(
            AlterCircle(ModeValue),
            TargetPath,
            SourceFormat=KPartFormatId,
            DestFormat="interchange.json",
            StrictMode=StrictMode,
            Overwrite=True,
        )
    assert TargetPath.read_bytes() == b"existing user destination"
