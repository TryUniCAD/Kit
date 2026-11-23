# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as KPythonPath


# native cancellation evidence requires an actual hidden console shared by launcher and supervisor
def RunConsole(ConfigPath: FilePath, SignalName: str) -> CompletedProcess[str]:
    from subprocess import CREATE_NEW_CONSOLE as KNewConsole
    from subprocess import STARTF_USESHOWWINDOW as KUseShowWindow
    from subprocess import STARTUPINFO as StartupInfo

    RootPath = FilePath(__file__).resolve().parents[4]
    WindowInfo = StartupInfo()
    setattr(WindowInfo, "dwFlags", KUseShowWindow)
    setattr(WindowInfo, "wShowWindow", 0)
    return RunProcess(
        [
            KPythonPath,
            "-m",
            "tests.Research.Windows.Cli.ConsoleLauncher",
            str(ConfigPath.parent / "ProcessIds.json"),
            str(RootPath),
            str(ConfigPath),
            SignalName,
        ],
        cwd=RootPath,
        creationflags=KNewConsole,
        startupinfo=WindowInfo,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
