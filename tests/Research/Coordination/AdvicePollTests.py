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


# idle provider contention must consume reads without serialized durable polling writes
def CheckAdvicePoll(TmpPath: FilePath) -> None:
    SourceFile = (
        FilePath(__file__).resolve().parents[3]
        / "re/automation/CodexAdvice/PollSmoke.py"
    )
    ResultInfo = RunProcess(
        [PythonExe, str(SourceFile), "--directory", str(TmpPath)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    assert '"read_only_polling": true' in ResultInfo.stdout
    assert '"live_provider_calls": 0' in ResultInfo.stdout
