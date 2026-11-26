# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from subprocess import run as RunProcess


# the replay fixture must use the exact approved seed implementation from the pinned stack
def CopySeedHelper(SourceRoot: FilePath, TargetPath: FilePath) -> None:
    Helper = RunProcess(
        [
            "git",
            "cat-file",
            "blob",
            "ff451cb90c337024401d87b9536275c07f43e9c2",
        ],
        cwd=SourceRoot,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    assert HashBytes(Helper).hexdigest() == (
        "3cf89358a5ec58935d75135b171383f562f7b7b5defc1359594bf72c0e248826"
    )
    _ = TargetPath.write_bytes(Helper)
