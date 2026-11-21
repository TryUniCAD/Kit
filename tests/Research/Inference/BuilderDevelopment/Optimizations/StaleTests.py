# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import PIPE as PipeStream, Popen as StartProcess, run as RunProcess
from time import monotonic as MonoTime, sleep as WaitBriefly
from tests.Research.Inference.BuilderDevelopment.Optimizations.PacketInputs import (
    WritePacket,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.ProbeInputs import (
    ProbeArgs,
)


# a stale local endpoint must prove its identity before the worker reveals any prompt or secret
def CheckPeerProof(TmpPath: FilePath) -> None:
    PacketPath = WritePacket(TmpPath)
    Command, EnvValue = ProbeArgs(TmpPath, "Stale", PacketPath, ActionName="stale")
    PeerProc = StartProcess(
        Command, env=EnvValue, stdout=PipeStream, stderr=PipeStream, text=True
    )
    try:
        Deadline = MonoTime() + 10
        while not (TmpPath / "Stale/PeerReady.json").is_file():
            assert PeerProc.poll() is None
            assert MonoTime() < Deadline
            WaitBriefly(0.01)
        Command, EnvValue = ProbeArgs(TmpPath, "Stale", PacketPath)
        Worker = RunProcess(
            Command, env=EnvValue, capture_output=True, text=True, timeout=20
        )
        assert Worker.returncode == 3, Worker.stdout + Worker.stderr
        ResultValue = DecodeJson(Worker.stdout)
        assert ResultValue["classification"].startswith("provider_")
        assert ResultValue["status"] != "candidate"
        Output, Errors = PeerProc.communicate(timeout=10)
        assert PeerProc.returncode == 0, Output + Errors
    finally:
        if PeerProc.poll() is None:
            PeerProc.terminate()
            PeerProc.wait(timeout=5)
    Frames = DecodeJson((TmpPath / "Stale/PeerFrames.json").read_bytes())
    assert Frames["closed_before_request"] is True
    assert Frames["extra_bytes"] == 0
    assert list(Frames["frames"][0]) == ["hello"]
    assert not (TmpPath / "Stale/Attempt/Candidate.json").exists()
