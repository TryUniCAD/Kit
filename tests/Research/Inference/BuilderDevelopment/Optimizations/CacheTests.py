# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import PIPE as PipeStream, Popen as StartProcess
from tests.Research.Inference.BuilderDevelopment.Optimizations.BrokerHarness import (
    BrokerHarness,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.PacketInputs import (
    WritePacket,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.ProbeInputs import (
    ProbeArgs,
)


# independent controller stores must coalesce identical work before either reserves another provider call
def CheckCoalesce(TmpPath: FilePath) -> None:
    PacketPath = WritePacket(TmpPath)
    with (
        BrokerHarness(TmpPath, "First", PacketPath),
        BrokerHarness(TmpPath, "Second", PacketPath),
    ):
        Workers = []
        for RunName in ("First", "Second"):
            Command, EnvValue = ProbeArgs(TmpPath, RunName, PacketPath)
            Workers.append(
                StartProcess(
                    Command,
                    env=EnvValue,
                    stdout=PipeStream,
                    stderr=PipeStream,
                    text=True,
                )
            )
        Outputs = [Worker.communicate(timeout=30) for Worker in Workers]
        assert all(Worker.returncode == 0 for Worker in Workers), Outputs
        Results = [DecodeJson(Output) for Output, _ in Outputs]
        assert sorted(Result["classification"] for Result in Results) == [
            "candidate_generated",
            "candidate_reused",
        ]
        Reused = next(
            Result
            for Result in Results
            if Result["classification"] == "candidate_reused"
        )
        assert Reused["usage"]["total_tokens"] == 0
        assert Reused["native_verified"] is False
    Calls = [
        DecodeJson(LineText)
        for LineText in (TmpPath / "ProviderCalls.jsonl").read_text().splitlines()
    ]
    assert (
        sum(
            CallRow.get("request", {}).get("method") == "turn/start"
            for CallRow in Calls
        )
        == 1
    )
    Reservations = []
    for RunName in ("First", "Second"):
        RunPath = TmpPath / RunName
        BudgetPath = RunPath / "ModelBudget.json"
        if BudgetPath.exists():
            Reservations.extend(DecodeJson(BudgetPath.read_bytes())["calls"])
        assert (RunPath / "Attempt/Packet.json").is_file()
        assert (RunPath / "Attempt/Candidate.json").is_file()
        assert (RunPath / "Attempt/Generation.json").is_file()
        Request = DecodeJson((RunPath / "Attempt/Request.json").read_bytes())
        if Request.get("reused_generation"):
            assert Request["reservation"] is None
            assert not BudgetPath.exists()
    assert len(Reservations) == 1
