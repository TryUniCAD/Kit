from tests.Convert.Solidworks.Research.AdapterBridge.AssertBridge import AssertBridge
from tests.Convert.Solidworks.Research.AdapterBridge.RunBridgePhase import (
    RunBridgePhase,
)
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)


# distinct authored parts exercise write options staged and named memory destinations plus public path ownership
def TestPartBridge() -> None:
    FirstValue = RunBridgePhase(BlindCaseInput("sdk bridge alpha", False))
    SecondValue = RunBridgePhase(BlindCaseInput("sdk 部品 bridge beta extended", True))
    assert AssertBridge(FirstValue) != AssertBridge(SecondValue)
