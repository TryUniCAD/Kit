# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import mark as TestMark


# policy process coverage must preserve exact historical notices without accepting altered legal commentary
@TestMark.parametrize(
    "AuthorText,PrefixText,ExitCode",
    (
        ("Parashell, Odin Glynn-Martin", "", 0),
        ("Odin Glynn-Martin, Stephen Harcourt, James Harcourt", "", 0),
        ("Altered Attribution", "", 1),
        ("Parashell, Odin Glynn-Martin", "\n", 1),
    ),
)
def CheckNoticeCli(
    TmpPath: FilePath, AuthorText: str, PrefixText: str, ExitCode: int
) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    SourceText = (RootPath / "Cli/KitCli/StartResearch.py").read_text(encoding="utf-8")
    SourcePath = TmpPath / "ResearchLaunch.py"
    _ = SourcePath.write_text(
        PrefixText + SourceText.replace("Parashell, Odin Glynn-Martin", AuthorText),
        encoding="utf-8",
    )
    ResultInfo = RunProcess(
        [KPythonPath, "-m", "tools.Steering.SteeringCompliance", str(SourcePath)],
        cwd=RootPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ResultInfo.returncode == ExitCode, (ResultInfo.stdout, ResultInfo.stderr)
    assert ("CMT001" in ResultInfo.stdout) is (ExitCode != 0)
