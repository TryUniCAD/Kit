# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from collections.abc import Sequence
from pathlib import Path as FilePath
from subprocess import CompletedProcess as ChildResult, run as RunProcess
from sys import executable as PythonExe

from tests.Research.SupervisorClient import KRepoRoot


# serialized case requests must exercise actual path validation and exclusive disk preparation
def RunBatchProbe(
    TmpPath: FilePath, OutputPath: FilePath, Cases: Sequence[object]
) -> ChildResult[str]:
    InputPath = TmpPath / "BatchInput.json"
    _ = InputPath.write_text(
        EncodeJson({"cases": Cases, "directory": str(OutputPath)}), encoding="utf-8"
    )
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(FilePath(__file__).with_name("BatchProbe.py")),
            str(InputPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
