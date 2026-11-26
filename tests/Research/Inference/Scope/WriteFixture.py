# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# synthetic immutable sessions exercise the actual worker without invoking a cad application
def WriteFixture(RootPath: FilePath, Variant: str) -> dict[FilePath, bytes]:
    RepoRoot = FilePath(__file__).resolve().parents[4]
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            str(RepoRoot / "re/automation/InferenceGrid/ProtocolFixture.py"),
            str(RootPath),
            Variant,
        ],
        cwd=RepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Process.returncode == 0, Process.stderr
    return {
        SourcePath: SourcePath.read_bytes()
        for SourcePath in RootPath.rglob("*")
        if SourcePath.is_file()
    }
