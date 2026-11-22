# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import CompletedProcess as ChildResult, run as RunProcess
from sys import executable as PythonExe

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Recipes.WriteRecipes import WriteRecipes


# preparation exercises the public runner while preserving the no native startup boundary
def RunCatalogue(TmpPath: FilePath, *Arguments: str | FilePath) -> ChildResult[str]:
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/InferenceGrid/RunFeatureCatalogue.py"),
            "--solidworks-catalogue",
            str(WriteRecipes(TmpPath)),
            "--directory",
            str(TmpPath / "Run"),
            "--author-samples",
            "--prepare-only",
            *map(str, Arguments),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
