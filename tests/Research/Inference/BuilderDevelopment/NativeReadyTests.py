# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from tests.Research.Inference.Authoring.Recipes.Windows.RunController import (
    RunController,
)
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.BuilderDevelopment.WriteInputs import WriteInputs


# explicit host readiness must rearm an existing controller without replacing prepared state
def CheckReady(TmpPath: FilePath) -> None:
    WriteInputs(TmpPath)
    Prepared = RunBuilder(TmpPath)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    StatePath = TmpPath / "Run/BuilderState.json"
    StateValue = DecodeJson(StatePath.read_bytes())
    StateValue["deadline"] = 0
    StatePath.write_text(EncodeJson(StateValue), encoding="utf-8")
    Configured = RunBuilder(
        TmpPath,
        "--builder-resume",
        "--solidworks-host",
        str(TmpPath / "Host.json"),
        IsPrepare=False,
    )
    assert Configured.returncode == 3, Configured.stdout + Configured.stderr
    StorePath = TmpPath / "Run/Store"
    Unavailable = RunController(
        StorePath,
        "resource",
        "application:solidworks:catalogue",
        "--unavailable",
        "--capacity",
        "1",
    )
    assert Unavailable.returncode == 0, Unavailable.stderr
    Resumed = RunBuilder(TmpPath, "--builder-resume", "--native-ready", IsPrepare=False)
    assert Resumed.returncode == 3, Resumed.stdout + Resumed.stderr
    Current = RunController(
        StorePath, "resource", "application:solidworks:catalogue", "--capacity", "1"
    )
    assert Current.returncode == 0, Current.stderr
    assert DecodeJson(Current.stdout)["available"] is True
    assert DecodeJson(StatePath.read_bytes())["jobs"] == {}
    assert not (TmpPath / "Run/NativeAttempts").exists()
