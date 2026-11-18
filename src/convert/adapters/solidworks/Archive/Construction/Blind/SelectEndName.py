from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.EndInput import KEndInput


# the authored primary label and fixed display identifier roles must share one binding rule
def SelectEndName(InputValue: KEndInput, OrdinalValue: int) -> str:
    if type(InputValue) is BlindEndInput and OrdinalValue == 1:
        return InputValue.DepthName
    return f"D{OrdinalValue}"
