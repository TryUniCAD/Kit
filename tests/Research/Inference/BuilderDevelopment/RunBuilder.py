# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import CompletedProcess as ChildResult, run as RunProcess
from sys import executable as PythonExe
from tests.Research.SupervisorClient import KRepoRoot


# real command execution exposes option validation and persistent resume behavior
def RunBuilder(
    TmpPath: FilePath,
    *ExtraArgs: str,
    IsAuto: bool = True,
    IsPrepare: bool = True,
    HasAuth: bool = True,
    HasMetadata: bool = True,
) -> ChildResult[str]:
    CommandArgs = [
        PythonExe,
        "-B",
        str(KRepoRoot / "re/automation/InferenceGrid/RunRecipeCampaign.py"),
        "--directory",
        str(TmpPath / "Run"),
        "--solidworks-catalogue",
        str(TmpPath / "FeaturePlan.json"),
    ]
    if IsAuto:
        CommandArgs += ["--auto-develop-builders"]
        if HasAuth:
            CommandArgs += [
                "--advisor",
                "ollama",
                "--auth",
                "local",
                "--model",
                "fixture-never-called",
            ]
        if HasMetadata:
            CommandArgs += ["--builder-api-metadata", str(TmpPath / "Api.json")]
    if IsPrepare:
        CommandArgs += ["--prepare-only"]
    return RunProcess(
        [*CommandArgs, *ExtraArgs],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=40,
    )
