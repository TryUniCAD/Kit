from tests.Convert.Solidworks.Research.Construction.AssertPolyBuild import (
    AssertPolyBuild,
)
from tests.Convert.Solidworks.Research.Construction.AssertPolyPrep import AssertPolyPrep
from tests.Convert.Solidworks.Research.Construction.BlindPartInput import BlindPartInput
from tests.Convert.Solidworks.Research.Construction.RunSketchPhase import RunSketchPhase


# different neutral ring sizes must generate and independently prepare complete streams through real process boundaries
def TestPolygonFlow() -> None:
    FirstInput = BlindPartInput(4, 0.018625)
    SecondInput = BlindPartInput(7, 0.031375)
    FirstBuild = RunSketchPhase(FirstInput, False)
    SecondBuild = RunSketchPhase(SecondInput, False)
    FirstLength = AssertPolyBuild(FirstBuild, 4)
    SecondLength = AssertPolyBuild(SecondBuild, 7)
    FirstPrepared = RunSketchPhase({"request": FirstInput, "build": FirstBuild}, True)
    SecondPrepared = RunSketchPhase(
        {"request": SecondInput, "build": SecondBuild}, True
    )
    AssertPolyPrep(FirstPrepared, FirstBuild, 4)
    AssertPolyPrep(SecondPrepared, SecondBuild, 7)
    assert SecondLength > FirstLength and FirstBuild["sha256"] != SecondBuild["sha256"]
