# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe, platform as HostPlatform

from pytest import mark as MarkValue


# full bootstrap subprocesses must confine their queue status and custom events to the selected owner home
@MarkValue.skipif(
    HostPlatform != "darwin", reason="private Fusion owner home requires macOS"
)
@MarkValue.parametrize(
    "CaseName",
    (
        "private",
        "linked-home",
        "public-home",
        "missing-home",
        "extra",
        "relative",
        "boolean-version",
        "duplicate",
        "array",
        "public-sidecar",
        "linked-sidecar",
        "oversize",
    ),
)
def CheckOwnerHome(TmpPath: FilePath, CaseName: str) -> None:
    RepoRoot = FilePath(__file__).resolve().parents[4]
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            str(RepoRoot / "re/automation/ApplicationWorkers/BootstrapHomeFixture.py"),
            str(TmpPath.resolve()),
            CaseName,
        ],
        cwd=RepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=25,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    assert ParseJson(Result.stdout) == {
        "case": CaseName,
        "status": "verified",
        "native_qualified": False,
    }
