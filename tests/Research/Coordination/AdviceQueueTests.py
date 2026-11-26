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


# historical provider evidence must not make abandoned callers exhaust bounded admission metadata
def CheckAdviceMeta(TmpPath: FilePath) -> None:
    SourceFile = (
        FilePath(__file__).resolve().parents[3]
        / "re/automation/CodexAdvice/MetadataSmoke.py"
    )
    ResultInfo = RunProcess(
        [PythonExe, str(SourceFile), "--directory", str(TmpPath)],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    assert '"metadata_checks": 3' in ResultInfo.stdout
    assert '"live_provider_calls": 0' in ResultInfo.stdout
