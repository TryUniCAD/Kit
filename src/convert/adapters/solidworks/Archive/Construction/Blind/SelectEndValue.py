from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.EndInput import KEndInput


# distinct second dimension values must survive whether the reverse direction participates in geometry
def SelectEndValue(InputValue: KEndInput, OrdinalValue: int) -> float:
    if OrdinalValue not in (1, 2):
        return 0.0
    if (
        OrdinalValue == 2
        and type(InputValue) is BossEndInput
        and InputValue.SecondDepth is not None
    ):
        return float(InputValue.SecondDepth)
    if (
        OrdinalValue == 2
        and type(InputValue) is BlindEndInput
        and InputValue.DormantDepth is not None
    ):
        return float(InputValue.DormantDepth)
    return float(InputValue.DepthValue)
