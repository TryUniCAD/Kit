# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ as ProcessEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from pytest import mark as TestMark

from tests.Research.SupervisorClient import KRepoRoot


# independent children must reject external paths before reading or publishing fixture artifacts
@TestMark.parametrize(
    "ScriptName",
    (
        "Authoring/Pipeline/FixtureCapture.py",
        "Authoring/Pipeline/ReadNeutral.py",
        "Authoring/Recipes/BatchCapture.py",
        "Authoring/Recipes/Windows/BatchProbe.py",
        "BuilderDevelopment/Generation/RunCleanup.py",
        "BuilderDevelopment/Optimizations/RunProbe.py",
        "BuilderDevelopment/QualificationProbe.py",
        "BuilderDevelopment/RegistryProbe.py",
        "BuilderDevelopment/StageProbe.py",
        "BuilderDevelopment/Transport/FixtureServer.py",
        "BuilderDevelopment/WorkerProbe.py",
    ),
)
def CheckPathFence(ScriptName: str) -> None:
    ScriptPath = KRepoRoot / "tests/Research/Inference" / ScriptName
    UnsafePath = FilePath.home() / "KitForbiddenFixture.json"
    ResultInfo = RunProcess(
        [PythonExe, "-B", str(ScriptPath), str(UnsafePath), str(UnsafePath)],
        cwd=KRepoRoot,
        env={**ProcessEnv, "PYTHONPATH": str(KRepoRoot)},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert ResultInfo.returncode != 0
    assert "path escapes trusted root" in ResultInfo.stderr, ResultInfo.stderr
