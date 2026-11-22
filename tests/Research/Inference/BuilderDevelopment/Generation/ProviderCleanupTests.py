# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from pytest import mark as CaseMark
from tests.Research.SupervisorClient import KRepoRoot


# real child completion and surviving descendants must retain honest provider outcomes
@CaseMark.parametrize(
    ("ModeName", "StopReason"),
    [
        ("exit", None),
        ("parentexit", None),
        ("descendant", "provider_timeout"),
        ("overflow", "provider_output_limit"),
    ],
)
def CheckCleanup(TmpPath: FilePath, ModeName: str, StopReason: str | None) -> None:
    ProcessInfo = RunProcess(
        [
            PythonExe,
            "-B",
            "-m",
            "tests.Research.Inference.BuilderDevelopment.Generation.RunCleanup",
            str(TmpPath),
            ModeName,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert ProcessInfo.returncode == 0, ProcessInfo.stdout + ProcessInfo.stderr
    ResultInfo = DecodeJson(ProcessInfo.stdout)
    assert ResultInfo["stop_reason"] == StopReason
    assert ResultInfo["owned_tree_termination_verified"] is True
    assert ResultInfo["child_still_live"] is False
    if StopReason is None:
        assert ResultInfo["returncode"] == 0
    if ModeName == "overflow":
        assert ResultInfo["capture"]["dropped_bytes"] > 0
        assert ResultInfo["capture"]["retained_bytes"] == 256
