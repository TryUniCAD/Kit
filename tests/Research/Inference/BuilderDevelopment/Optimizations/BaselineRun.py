# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from time import monotonic as MonoTime

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    ReadRecord,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.PacketInputs import (
    WritePacket,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.ProbeInputs import (
    ProbeArgs,
)


# a successful control measures ordinary fixture turnaround before asserting that another worker is blocked
def TimedBaseline(TmpPath: FilePath) -> float:
    PacketPath = WritePacket(TmpPath, "BaselinePacket")
    Command, EnvValue = ProbeArgs(
        TmpPath, "Waiting", PacketPath, AttemptName="Baseline"
    )
    StartedAt = MonoTime()
    Process = RunProcess(
        Command, env=EnvValue, capture_output=True, text=True, timeout=30
    )
    Elapsed = MonoTime() - StartedAt
    assert Process.returncode == 0, Process.stdout + Process.stderr
    assert ReadRecord(Process.stdout)["classification"] == "candidate_generated"
    return Elapsed
