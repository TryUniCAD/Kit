from __future__ import annotations

from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.convert.solidworks.research.FreshPartRunner import RunFreshPart
from tests.convert.solidworks.research.FreshPartTests import AssertPart
from tests.convert.solidworks.research.LockedPartInput import LockedPartInput
from tests.convert.solidworks.research.PartArtifacts import SavePartOutput

KRepoRoot = FilePath(__file__).resolve().parents[4]
KLockPath = KRepoRoot / "re/solidworks/v2026/heldout/polygon/Lock.json"


def TestLockedParts() -> None:
    LockData = CastValue(dict[str, object], LoadJson(KLockPath.read_text()))
    Records = CastValue(list[dict[str, object]], LockData["records"])
    assert len(Records) == 5
    for RecordData in Records:
        Request = LockedPartInput(RecordData)
        Report = RunFreshPart(Request)
        ModelData = CastValue(dict[str, object], Request["document"])
        Vertices = CastValue(list[list[float]], ModelData["vertices_m"])
        AssertPart(Report, len(Vertices), CastValue(float, ModelData["depth_m"]))
        SavePartOutput(CastValue(str, ModelData["name"]), Request, Report)
