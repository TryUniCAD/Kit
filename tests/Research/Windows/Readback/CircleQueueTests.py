# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from sys import platform as HostPlatform
from typing import cast as CastValue

from pytest import mark as TestMark

from tests.Research.Windows.Readback.InstallReadback import InstallReadback
from tests.Research.Windows.Readback.QueueReadback import QueueReadback


# circular completion requires every binding and distinct observed file before copied evidence is accepted
@TestMark.skipif(HostPlatform != "win32", reason="Windows readback process boundary")
@TestMark.parametrize(
    "FaultName", ("none", "circle", "roster", "chain", "binding", "stage", "incomplete")
)
def CheckCircleQueue(TmpPath: FilePath, FaultName: str) -> None:
    RootPath, ConfigPath = InstallReadback(TmpPath)
    Result = QueueReadback(TmpPath, RootPath, ConfigPath, FaultName)
    Records = CastValue(dict[str, object], Result["records"])
    assert Records["native_qualified"] is False
    if FaultName != "none":
        assert Result["outcome"] == "waiting_application", Result
        Expected = (
            "lacks complete source"
            if FaultName in ("circle", "roster")
            else "native progress"
        )
        assert Expected in str(Result["reason"])
        assert "artifacts" not in Result
        assert (TmpPath / "Endpoint/fence.json").exists()
        return
    assert Result["outcome"] == "completed", Result
    assert Records["phase"] == "p02-readback"
    Artifacts = CastValue(dict[str, object], Result["artifacts"])
    assert set(Artifacts) == {
        "readback.plan",
        "readback.measurements",
        "readback.receipt",
        "dispatch",
    }
    Receipt = DecodeJson((TmpPath / "Session/work/readback/receipt.json").read_bytes())
    assert Receipt["observed_files"] == Receipt["circle_bindings_verified"] == 5
    Dispatch = DecodeJson((TmpPath / "Session/work/dispatch.json").read_bytes())
    assert Dispatch["proof"]["fixture_only"] is True
    assert Dispatch["proof"]["native_progress_events"] == 3
    assert (TmpPath / "Endpoint/fence.json").exists()
