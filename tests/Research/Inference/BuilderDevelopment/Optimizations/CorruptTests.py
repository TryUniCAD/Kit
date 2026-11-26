# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
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
    AsRecord,
    ReadRecord as DecodeJson,
)


# corrupted cache evidence must block new spending and release ownership for a later valid reader
def CheckCorrupt(TmpPath: FilePath) -> None:
    PacketPath = WritePacket(TmpPath)
    with BrokerHarness(TmpPath, "Original", PacketPath):
        Command, EnvValue = ProbeArgs(TmpPath, "Original", PacketPath)
        Original = RunProcess(
            Command, env=EnvValue, capture_output=True, text=True, timeout=30
        )
        assert Original.returncode == 0, Original.stdout + Original.stderr
    CachePath = next((TmpPath / "Shared").glob("*.json"))
    CacheBytes = CachePath.read_bytes()
    _ = CachePath.write_text("{", encoding="utf-8")
    with BrokerHarness(TmpPath, "Corrupt", PacketPath):
        Command, EnvValue = ProbeArgs(TmpPath, "Corrupt", PacketPath)
        Corrupt = RunProcess(
            Command, env=EnvValue, capture_output=True, text=True, timeout=30
        )
        assert Corrupt.returncode == 3, Corrupt.stdout + Corrupt.stderr
        assert (
            DecodeJson(Corrupt.stdout)["classification"] == "generation_cache_invalid"
        )
        assert not (TmpPath / "Corrupt/ModelBudget.json").exists()
    _ = CachePath.write_bytes(CacheBytes)
    with BrokerHarness(TmpPath, "Restored", PacketPath):
        Command, EnvValue = ProbeArgs(TmpPath, "Restored", PacketPath)
        Restored = RunProcess(
            Command, env=EnvValue, capture_output=True, text=True, timeout=30
        )
        assert Restored.returncode == 0, Restored.stdout + Restored.stderr
        assert DecodeJson(Restored.stdout)["classification"] == "candidate_reused"
        assert not (TmpPath / "Restored/ModelBudget.json").exists()
    Calls = [
        DecodeJson(LineText)
        for LineText in (TmpPath / "ProviderCalls.jsonl").read_text().splitlines()
    ]
    assert (
        sum(
            AsRecord(CallRow.get("request", {})).get("method") == "turn/start"
            for CallRow in Calls
        )
        == 1
    )
