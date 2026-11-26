# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from ast import Raise as RaiseNode
from ast import parse as ParseCode
from json import loads as ReadJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess
from sys import platform as SysPlatform
from typing import cast as CastValue

from tests.Research.Archives.FusionBossRequest.NativeWitness.ArtifactPin import (
    ArtifactPin,
)


# offline preparation may seal custody but must leave native process evidence unclaimed
def CheckPlanStage(
    PlanRoot: FilePath, Result: CompletedProcess[str]
) -> dict[str, object]:
    assert Result.returncode == 0, Result.stderr
    Receipt = CastValue(dict[str, object], ReadJson(Result.stdout))
    PlanPath = PlanRoot / "plan.json"
    PlanData = CastValue(dict[str, object], ReadJson(PlanPath.read_bytes()))
    assert Receipt["plan_sha256"] == ArtifactPin(PlanPath)[0]
    assert PlanData["schema"] == 2 and PlanData["fusion_version"] == "2706.1.17"
    if SysPlatform == "darwin":
        assert Receipt["status"] == "prepared_for_licensed_fusion"
        assert Receipt["preparation_host"] == "licensed_macos"
    else:
        assert Receipt["status"] == "prepared_p03_custody_offline"
        assert Receipt["preparation_host"] == (
            "offline_windows" if SysPlatform == "win32" else "offline_other"
        )
    assert PlanData["preparation_host"] == Receipt["preparation_host"]
    assert PlanData["candidate"] == Receipt["candidate"]
    assert {Entry.name for Entry in PlanRoot.iterdir()} == {
        "plan.json",
        "inputs",
        "phase-a.py",
        "phase-b.py",
    }
    for Phase in ("a", "b"):
        Script = (PlanRoot / f"phase-{Phase}.py").read_text(encoding="utf-8")
        TreeValue = ParseCode(Script)
        assert TreeValue.body
        if SysPlatform != "darwin":
            (Statement,) = TreeValue.body
            assert isinstance(Statement, RaiseNode)
            assert (
                f"P03 phase {Phase} of plan {Receipt['plan_sha256']} is offline-only"
                in Script
            )
    return PlanData
