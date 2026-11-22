# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path


# invalid installation files let the real shell prove admission failure before any application can launch
def ShellInterop(RootPath: Path) -> tuple[Path, Path]:
    NativePath = RootPath / "RejectedExecutable.exe"
    InteropPath = RootPath / "SolidWorks.Interop.sldworks.dll"
    NativePath.touch(exist_ok=False)
    InteropPath.touch(exist_ok=False)
    return NativePath, InteropPath
