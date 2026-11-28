# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from subprocess import run
from sys import executable

from pytest import mark

from tests.Research.SupervisorClient import KRepoRoot


# fresh processes bind the new verifier to complete retained native measurement receipts
@mark.parametrize("RecipeKey", ("P01", "P02", "P03", "P04", "P05"))
def CheckSavedShape(RecipeKey: str) -> None:
    Process = run(
        [executable, "-B", str(Path(__file__).with_name("ReadSaved.py")), RecipeKey],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode == 0, Process.stderr
    assert Process.stdout.strip() == RecipeKey + " retained native geometry matched"
