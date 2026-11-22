# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.BuilderDevelopment.WriteInputs import WriteInputs


# preparation and host recovery must preserve hidden cases without dispatching fixtures
def CheckProvision(TmpPath: FilePath) -> None:
    WriteInputs(TmpPath)
    Prepared = RunBuilder(TmpPath)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    JobPath = TmpPath / "Run/BuilderJob.json"
    JobBytes = JobPath.read_bytes()
    StatePath = TmpPath / "Run/BuilderState.json"
    BeforeState = DecodeJson(StatePath.read_bytes())
    MissingHost = RunBuilder(TmpPath, "--builder-resume", IsPrepare=False)
    assert MissingHost.returncode == 3, MissingHost.stdout + MissingHost.stderr
    assert DecodeJson(MissingHost.stdout)["classification"].startswith(
        "licensed_host_unavailable"
    )
    Current = DecodeJson(StatePath.read_bytes())
    Current["deadline"] = 0
    _ = StatePath.write_text(EncodeJson(Current), encoding="utf-8")
    Resumed = RunBuilder(
        TmpPath,
        "--builder-resume",
        "--solidworks-host",
        str(TmpPath / "Host.json"),
        IsPrepare=False,
    )
    assert Resumed.returncode == 3, Resumed.stdout + Resumed.stderr
    assert DecodeJson(Resumed.stdout)["classification"] == "time_budget_exhausted"
    assert (TmpPath / "Run/Supervisor.json").is_file()
    AfterState = DecodeJson(StatePath.read_bytes())
    assert AfterState["reservations"] == BeforeState["reservations"]
    assert AfterState["attempts"] == BeforeState["attempts"] == []
    assert JobPath.read_bytes() == JobBytes
    assert not (TmpPath / "Run/Generation").exists()
    assert not (TmpPath / "Run/NativeAttempts").exists()
