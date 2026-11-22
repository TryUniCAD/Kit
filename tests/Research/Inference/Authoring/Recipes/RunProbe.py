# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess as ChildResult, run as RunProcess
from sys import executable as PythonExe

from tests.Research.SupervisorClient import KRepoRoot


# a separate interpreter exercises recipe contracts without importing native application workers
def RunProbe(TmpPath: FilePath, Action: str, Payload: object) -> ChildResult[str]:
    InputPath = TmpPath / "ProbeInput.json"
    _ = InputPath.write_text(EncodeJson(Payload), encoding="utf-8")
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(FilePath(__file__).with_name("RecipeProbe.py")),
            Action,
            str(InputPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
