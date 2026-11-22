# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess


# source admission needs genuine git objects isolated from the caller checkout
def ReadbackGit(RootPath: FilePath, *Arguments: str) -> str:
    return RunProcess(
        ["git", "-C", str(RootPath), *Arguments],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    ).stdout.strip()
