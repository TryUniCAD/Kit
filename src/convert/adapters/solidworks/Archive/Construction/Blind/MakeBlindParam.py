from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.EndInput import KEndInput
from convert.adapters.solidworks.Archive.Construction.Blind.SelectEndName import (
    SelectEndName,
)
from convert.adapters.solidworks.Archive.Construction.Blind.SelectEndValue import (
    SelectEndValue,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# native parameter factories derive their class name and value from the selected blind dimension role
def MakeBlindParam(InputValue: KEndInput, OrdinalValue: int) -> ArchiveNode:
    if type(CastValue(object, InputValue)) not in (BlindEndInput, BossEndInput):
        raise TypeError("blind parameter requires validated neutral inputs")
    if type(CastValue(object, OrdinalValue)) is not int or OrdinalValue not in (
        1,
        2,
        3,
        4,
        19,
    ):
        raise ValueError("blind parameter ordinal must be D1 D2 D3 D4 or D19")
    ClassName = (
        "moAngleParameter_c" if OrdinalValue in (3, 4) else "moLengthParameter_c"
    )
    NativeValue = SelectEndValue(InputValue, OrdinalValue)
    NameValue = ArchiveNode(
        RuntimeClass("moNodeName_c", 1),
        {"f08": SelectEndName(InputValue, OrdinalValue)},
    )
    return ArchiveNode(
        RuntimeClass(ClassName, 1),
        {
            "f18": NameValue,
            "f0c": 0,
            "f28": 0x40000000,
            "f08": -1,
            "f2c": 0,
            "f20": "",
            "f48": None,
            "f58": NativeValue,
            "f68": 0,
        },
    )
