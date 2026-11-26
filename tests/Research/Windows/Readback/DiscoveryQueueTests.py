# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from sys import platform as HostPlatform

from pytest import mark as TestMark

from tests.Research.Windows.Readback.InstallReadback import InstallReadback
from tests.Research.Windows.Readback.QueueReadback import QueueReadback


# a combined request must preserve each family and the collector command state evidence across dispatch
@TestMark.skipif(HostPlatform != "win32", reason="Windows readback process boundary")
@TestMark.parametrize(
    "FaultName,ExpectedReason",
    (
        ("none", ""),
        ("scope", "exact profile and verified cut rosters"),
        ("duplicate", "lacks complete source"),
        ("cut", "exact profile and verified cut rosters"),
        ("restore", "restored command batching state"),
        ("command_inactive", "restored command batching state"),
    ),
)
def CheckDiscovery(TmpPath: FilePath, FaultName: str, ExpectedReason: str) -> None:
    RootPath, ConfigPath = InstallReadback(TmpPath)
    Result = QueueReadback(
        TmpPath, RootPath, ConfigPath, FaultName, "p01-p03-p04-readback"
    )
    if ExpectedReason:
        assert Result["outcome"] == "waiting_application", Result
        assert ExpectedReason in str(Result["reason"])
        assert "artifacts" not in Result
        return
    assert Result["outcome"] == "completed", Result
    Outputs = TmpPath / "Session/work"
    Receipt = DecodeJson((Outputs / "readback/receipt.json").read_bytes())
    Dispatch = DecodeJson((Outputs / "dispatch.json").read_bytes())
    assert Receipt["observed_files"] == Receipt["discovery_files_observed"] == 25
    assert Dispatch["proof"]["phase"] == "p01-p03-p04-readback"
