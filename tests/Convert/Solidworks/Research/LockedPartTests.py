from __future__ import annotations

from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.FreshPartTests import AssertPart
from tests.Convert.Solidworks.Research.LockedPartInput import LockedPartInput
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput

# repository resolution keeps child processes independent from the invoking working directory
KRepoRoot = FilePath(__file__).resolve().parents[4]

# the preexisting lock separates held out inputs from recovered grammar
KLockPath = KRepoRoot / "re/solidworks/v2026/heldout/polygon/Lock.json"


# locked inputs preserve an auditable boundary between grammar recovery and later verification
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
