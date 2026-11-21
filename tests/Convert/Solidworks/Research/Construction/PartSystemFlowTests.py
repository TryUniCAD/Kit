from tests.Convert.Solidworks.Research.Construction.AssertSystem import AssertSystem
from tests.Convert.Solidworks.Research.Construction.RunSystemPhase import RunSystemPhase
from tests.Convert.Solidworks.Research.Construction.SystemCaseInput import (
    SystemCaseInput,
)


# varied neutral configurations and system topology must survive guarded sdk construction and independent complete stream preparation
def TestPartSystem() -> None:
    FirstInput = SystemCaseInput("sdk system alpha", False)
    SecondInput = SystemCaseInput("sdk 部品 system beta extended", True)
    FirstBuild = RunSystemPhase(FirstInput, False)
    SecondBuild = RunSystemPhase(SecondInput, False)
    FirstPrepared = RunSystemPhase({"request": FirstInput, "build": FirstBuild}, True)
    SecondPrepared = RunSystemPhase(
        {"request": SecondInput, "build": SecondBuild}, True
    )
    FirstLength = AssertSystem(FirstBuild, FirstPrepared, 1)
    SecondLength = AssertSystem(SecondBuild, SecondPrepared, 3)
    assert FirstLength != SecondLength
