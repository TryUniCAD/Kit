from tests.Convert.Solidworks.Research.AdapterBridge.AssertBridge import AssertBridge
from tests.Convert.Solidworks.Research.AdapterBridge.RunBridgePhase import (
    RunBridgePhase,
)
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)


# distinct authored neutral parts must exercise standard write options staged and memory destinations and public read only behavior through the real sdk
def TestPartBridge() -> None:
    FirstValue = RunBridgePhase(BlindCaseInput("sdk bridge alpha", False))
    SecondValue = RunBridgePhase(BlindCaseInput("sdk 部品 bridge beta extended", True))
    assert AssertBridge(FirstValue) != AssertBridge(SecondValue)
