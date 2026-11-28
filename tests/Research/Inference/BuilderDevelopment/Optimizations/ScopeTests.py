# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from pytest import mark as CaseMark
from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.BuilderDevelopment.Optimizations.BrokerHarness import (
    BrokerHarness,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.ChangedSources import (
    CopyChanged,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.PacketInputs import (
    WritePacket,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.ProbeInputs import (
    ProbeArgs,
)

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    AsRecord,
    ReadRecord as DecodeJson,
)


# cache scope must follow actual request model schema and source boundaries across independent processes
@CaseMark.parametrize("ChangeKind", ["packet", "model", "source", "schema"])
def CheckScope(TmpPath: FilePath, ChangeKind: str) -> None:
    PacketPath = WritePacket(TmpPath)
    with BrokerHarness(TmpPath, "Original", PacketPath):
        Command, EnvValue = ProbeArgs(TmpPath, "Original", PacketPath)
        Original = RunProcess(
            Command, env=EnvValue, capture_output=True, text=True, timeout=30
        )
        assert Original.returncode == 0, Original.stdout + Original.stderr
    ModelName = "gpt-6.1-sol" if ChangeKind == "model" else "gpt-6.1-terra"
    SourceRoot = KRepoRoot
    if ChangeKind == "packet":
        PacketPath = WritePacket(TmpPath, "ChangedPacket")
    if ChangeKind in ("source", "schema"):
        SourceRoot = CopyChanged(TmpPath, ChangeKind)
    with BrokerHarness(
        TmpPath, "Changed", PacketPath, ModelName, SourceRoot=SourceRoot
    ):
        Command, EnvValue = ProbeArgs(
            TmpPath, "Changed", PacketPath, ModelName, SourceRoot=SourceRoot
        )
        Changed = RunProcess(
            Command, env=EnvValue, capture_output=True, text=True, timeout=30
        )
        assert Changed.returncode == 0, Changed.stdout + Changed.stderr
        Result = DecodeJson(Changed.stdout)
        assert Result["classification"] == "candidate_generated"
        assert AsRecord(Result.get("cache", {})).get("hit") is False
    Calls = [
        DecodeJson(LineText)
        for LineText in (TmpPath / "ProviderCalls.jsonl").read_text().splitlines()
    ]
    assert (
        sum(
            AsRecord(CallRow.get("request", {})).get("method") == "turn/start"
            for CallRow in Calls
        )
        == 2
    )
