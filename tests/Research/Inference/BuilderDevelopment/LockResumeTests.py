# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import PIPE as PipeStream, Popen as StartProcess
from sys import executable as PythonExe
from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.BuilderDevelopment.WriteInputs import WriteInputs


# competing resumes must not change budgets or clear a pause before obtaining ownership
def CheckLocked(TmpPath: FilePath) -> None:
    WriteInputs(TmpPath)
    Prepared = RunBuilder(TmpPath)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    RunPath = TmpPath / "Run"
    PausePath = RunPath / "CataloguePause.json"
    PausePath.write_text('{"paused":true}', encoding="utf-8")
    StateBytes = (RunPath / "BuilderState.json").read_bytes()
    PauseBytes = PausePath.read_bytes()
    ScriptPath = KRepoRoot / "tests/Research/Inference/BuilderDevelopment/HoldRun.py"
    Owner = StartProcess(
        [PythonExe, "-B", str(ScriptPath), str(RunPath)],
        stdin=PipeStream,
        stdout=PipeStream,
        stderr=PipeStream,
        text=True,
    )
    try:
        assert Owner.stdout.readline().strip() == "ready"
        Process = RunBuilder(
            TmpPath, "--builder-resume", "--builder-extra-attempts", "1"
        )
        assert Process.returncode != 0
        assert (RunPath / "BuilderState.json").read_bytes() == StateBytes
        assert PausePath.read_bytes() == PauseBytes
    finally:
        Owner.communicate("\n", timeout=10)
