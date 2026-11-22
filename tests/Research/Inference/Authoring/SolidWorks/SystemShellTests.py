# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from sys import platform

from pytest import MonkeyPatch as PatchScope, mark as TestMark

from tests.Research.Inference.Authoring.SolidWorks.SystemShell import SystemShell


# untrusted environment overrides must never redirect the actual native compiler shell
@TestMark.skipif(platform != "win32", reason="Windows system directory API")
def CheckShellPath(TmpPath: Path, MonkeyPatch: PatchScope) -> None:
    MonkeyPatch.setenv("SystemRoot", str(TmpPath))
    ShellPath = SystemShell()
    assert ShellPath.name.lower() == "powershell.exe"
    assert ShellPath.parent.name == "v1.0"
    assert ShellPath.is_file()
    assert not ShellPath.is_relative_to(TmpPath)
