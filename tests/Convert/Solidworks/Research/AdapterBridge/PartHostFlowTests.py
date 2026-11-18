from tests.Convert.Solidworks.Research.AdapterBridge.AssertHostPath import (
    AssertHostPath,
)
from tests.Convert.Solidworks.Research.AdapterBridge.RunHostPhase import RunHostPhase
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)


# separately authored standalone parts must preserve complete candidate bytes across host destinations without admitting unsupported bundle or external reference semantics
def TestPartHost() -> None:
    FirstValue = RunHostPhase(BlindCaseInput("sdk host alpha", False))
    SecondValue = RunHostPhase(BlindCaseInput("sdk 部品 host beta extended", True))
    assert AssertHostPath(FirstValue) != AssertHostPath(SecondValue)
