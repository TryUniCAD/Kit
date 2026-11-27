# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
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


# installed bootstrap subprocesses must isolate git authority before any licensed application operation
@MarkValue.skipif(HostPlatform != "win32", reason="Windows embedded bootstrap")
@MarkValue.parametrize(
    "CaseName",
    (
        "baseline",
        "git-directory",
        "git-worktree",
        "git-objects",
        "git-config",
        "git-global",
        "git-system",
        "git-grafts",
        "git-replacements",
        "dirty-protocol",
        "installed-mismatch",
        "installation-root",
        "no-opt-in",
        "downstream-dirty",
    ),
)
def CheckGitHost(TmpPath: FilePath, CaseName: str) -> None:
    RepoRoot = FilePath(__file__).resolve().parents[4]
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            str(RepoRoot / "re/automation/ApplicationWorkers/BootstrapGitFixture.py"),
            str(TmpPath.resolve()),
            CaseName,
        ],
        cwd=RepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    assert ParseJson(Result.stdout) == {
        "case": CaseName,
        "status": "verified",
        "native_qualified": False,
    }
