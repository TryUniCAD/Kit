# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
import subprocess
import sys

from tests.Research.SupervisorClient import KRepoRoot


# process boundaries cover the actual controller and feature command entry points
def InvokeAuto(Script: str, *Arguments: str | Path, Expected: int = 0) -> str:
    Result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(KRepoRoot / "re/automation" / Script),
            *map(str, Arguments),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=150,
    )
    assert Result.returncode == Expected, Result.stderr
    return Result.stdout if Expected == 0 else Result.stderr
