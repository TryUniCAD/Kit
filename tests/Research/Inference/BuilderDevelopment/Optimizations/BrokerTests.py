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
from pytest import mark as CaseMark
from tests.Research.Inference.BuilderDevelopment.Optimizations.BrokerHarness import (
    BrokerHarness,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.PacketInputs import (
    WritePacket,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.ProbeInputs import (
    ProbeArgs,
)


# invalid local clients must be rejected without creating a model session or consuming a reservation
@CaseMark.parametrize(
    "ModeName",
    [
        "token",
        "remote",
        "schema",
        "oversized",
        "incomplete",
        "queued",
        "owner",
        "recordshape",
        "instructions",
    ],
)
def CheckReject(TmpPath: FilePath, ModeName: str) -> None:
    PacketPath = WritePacket(TmpPath)
    with BrokerHarness(TmpPath, "Rejected", PacketPath):
        Command, EnvValue = ProbeArgs(
            TmpPath, "Rejected", PacketPath, ActionName=ModeName
        )
        Process = RunProcess(
            Command, env=EnvValue, capture_output=True, text=True, timeout=20
        )
        assert Process.returncode == 0, Process.stdout + Process.stderr
        assert "provider_" in DecodeJson(Process.stdout)["error"]
        assert not (TmpPath / "ProviderCalls.jsonl").exists()
        assert not (TmpPath / "Rejected/ModelBudget.json").exists()
