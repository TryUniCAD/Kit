# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import PIPE as PipeStream, Popen as StartProcess
from time import monotonic as MonoTime, sleep as WaitBriefly
from tests.Research.Inference.BuilderDevelopment.Optimizations.BaselineRun import (
    TimedBaseline,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.BlockedProof import (
    ProveBlocked,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.BrokerHarness import (
    BrokerHarness,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.PacketInputs import (
    WritePacket,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.ProbeInputs import (
    ProbeArgs,
)

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    ReadRecord as DecodeJson,
)


# terminating a lock owner must let another real worker proceed without deleting coordination files
def CheckOwnerExit(TmpPath: FilePath) -> None:
    PacketPath = WritePacket(TmpPath)
    Command, EnvValue = ProbeArgs(TmpPath, "Owner", PacketPath, ActionName="hold")
    Owner = StartProcess(
        Command,
        env=EnvValue,
        stdin=PipeStream,
        stdout=PipeStream,
        stderr=PipeStream,
        text=True,
    )
    try:
        Deadline = MonoTime() + 10
        while not (TmpPath / "Owner/OwnerReady.json").is_file():
            assert Owner.poll() is None
            assert MonoTime() < Deadline
            WaitBriefly(0.01)
        with BrokerHarness(TmpPath, "Waiting", PacketPath):
            NormalSeconds = TimedBaseline(TmpPath)
            Command, EnvValue = ProbeArgs(TmpPath, "Waiting", PacketPath)
            Worker = StartProcess(
                Command,
                env=EnvValue,
                stdout=PipeStream,
                stderr=PipeStream,
                text=True,
            )
            ProveBlocked(Worker, TmpPath, NormalSeconds)
            Owner.terminate()
            _ = Owner.wait(timeout=5)
            Output, Errors = Worker.communicate(timeout=30)
            assert Worker.returncode == 0, Output + Errors
            assert DecodeJson(Output)["classification"] == "candidate_generated"
    finally:
        if Owner.poll() is None:
            _ = Owner.communicate("release\n", timeout=5)
