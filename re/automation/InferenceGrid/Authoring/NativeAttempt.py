# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path


# native failure evidence must survive ordinary supervisor cleanup without exposing another run or user session
def MakeNativePath(SessionPath, HostPath):
    SessionPath = Path(SessionPath).resolve(strict=True)
    HostPath = Path(HostPath).resolve(strict=True)
    if not SessionPath.is_dir() or not HostPath.is_file():
        raise ValueError(
            "native attempt requires its session directory and prepared host file"
        )
    RunRoot = HostPath.parent
    if not SessionPath.is_relative_to(RunRoot):
        raise ValueError("native attempt must belong to its prepared host run")
    Attempts = RunRoot / "NativeAttempts"
    if Attempts.is_symlink() or (
        Attempts.exists() and not Attempts.resolve(strict=True).is_relative_to(RunRoot)
    ):
        raise ValueError("native attempt archive escapes its prepared run")
    Attempts.mkdir(mode=0o700, exist_ok=True)
    AttemptPath = Attempts / SessionPath.name
    AttemptPath.mkdir(mode=0o700)
    return AttemptPath / "Capture"
