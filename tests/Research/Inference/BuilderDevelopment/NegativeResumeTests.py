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


# restarting must never turn a saved false acceptance into permission for paid generation
def CheckNegGate(TmpPath: FilePath) -> None:
    WriteInputs(TmpPath)
    Prepared = RunBuilder(TmpPath, "--builder-negative-probe")
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    StatePath = TmpPath / "Run/BuilderState.json"
    StateValue = DecodeJson(StatePath.read_bytes())
    StateValue["negative_probe"] = {
        "verdict": {"verified": True, "classification": "fixture_false_accept"},
        "verification_job": "unlicensed-fixture",
    }
    StateValue["attempt_limit"] = 0
    _ = StatePath.write_text(EncodeJson(StateValue), encoding="utf-8")
    _ = (TmpPath / "Run/Supervisor.json").write_text("{}", encoding="utf-8")
    for _ in range(2):
        Resumed = RunBuilder(TmpPath, "--builder-resume", IsPrepare=False)
        assert Resumed.returncode == 3, Resumed.stdout + Resumed.stderr
        ResultInfo = DecodeJson(Resumed.stdout)
        assert ResultInfo["classification"] == "verifier_false_accept", ResultInfo
        assert ResultInfo["builder_qualified"] is False
        assert ResultInfo["jobs"] == {}
        assert not (TmpPath / "Run/Generation").exists()
