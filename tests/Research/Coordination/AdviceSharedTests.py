# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from sys import platform as PlatformName


# independent advice processes must share calls and preserve uncertain charges across interruption
def CheckAdviceFlow(TmpPath: FilePath) -> None:
    SourceFile = (
        FilePath(__file__).resolve().parents[3]
        / "re/automation/CodexAdvice/SharedSmoke.py"
    )
    CommandList = [PythonExe, str(SourceFile), "--directory", str(TmpPath)]
    if PlatformName == "win32":
        CommandList.extend(["--child", "--name", "Unsupported"])
    ResultInfo = RunProcess(
        CommandList, capture_output=True, text=True, check=False, timeout=60
    )
    if PlatformName == "win32":
        assert ResultInfo.returncode != 0
        assert "owner-private local POSIX directory" in ResultInfo.stderr
    else:
        assert ResultInfo.returncode == 0, ResultInfo.stderr
        assert '"checks": 5' in ResultInfo.stdout
        assert '"live_provider_calls": 0' in ResultInfo.stdout
