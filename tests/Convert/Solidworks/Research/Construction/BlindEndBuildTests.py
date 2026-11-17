from tests.Convert.Solidworks.Research.Construction.AssertBlindCase import (
    AssertBlindCase,
)
from tests.Convert.Solidworks.Research.Construction.BlindPartInput import BlindPartInput
from tests.Convert.Solidworks.Research.Construction.RunBlindCase import RunBlindCase


# fresh parameter and end owners must synthesize different input topologies through real native stream composition
def TestBlindEnds() -> None:
    FirstDepth, SecondDepth = 0.019625, 0.027375
    FirstReport = RunBlindCase(BlindPartInput(4, FirstDepth))
    SecondReport = RunBlindCase(BlindPartInput(7, SecondDepth))
    FirstLength = AssertBlindCase(FirstReport, FirstDepth)
    SecondLength = AssertBlindCase(SecondReport, SecondDepth)
    assert (
        SecondLength > FirstLength and FirstReport["sha256"] != SecondReport["sha256"]
    )
