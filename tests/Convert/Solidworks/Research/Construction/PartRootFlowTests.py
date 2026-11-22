from tests.Convert.Solidworks.Research.Construction.AssertRootFlow import AssertRootFlow
from tests.Convert.Solidworks.Research.Construction.RootCaseInput import RootCaseInput
from tests.Convert.Solidworks.Research.Construction.RunRootPhase import RunRootPhase


# distinct authored metadata and reservation state must reach complete native root streams and independent preparation
def TestPartRoot() -> None:
    FirstInput = RootCaseInput("sdk root alpha", 0, (0, 3))
    SecondInput = RootCaseInput("sdk 部品 root beta", 17, (17, 18, 20))
    FirstBuild = RunRootPhase(FirstInput, False)
    SecondBuild = RunRootPhase(SecondInput, False)
    FirstPrepared = RunRootPhase({"request": FirstInput, "build": FirstBuild}, True)
    SecondPrepared = RunRootPhase({"request": SecondInput, "build": SecondBuild}, True)
    FirstLength = AssertRootFlow(FirstBuild, FirstPrepared, 1, 2)
    SecondLength = AssertRootFlow(SecondBuild, SecondPrepared, 19, 21)
    assert FirstLength != SecondLength
