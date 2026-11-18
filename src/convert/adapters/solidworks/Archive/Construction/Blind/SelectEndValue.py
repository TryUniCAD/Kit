from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.EndInput import KEndInput


# an inactive reverse display uses the primary constructor depth and an active reverse display uses its own modeled depth
def SelectEndValue(InputValue: KEndInput, OrdinalValue: int) -> float:
    if OrdinalValue not in (1, 2):
        return 0.0
    if (
        OrdinalValue == 2
        and type(InputValue) is BossEndInput
        and InputValue.SecondDepth is not None
    ):
        return float(InputValue.SecondDepth)
    return float(InputValue.DepthValue)
