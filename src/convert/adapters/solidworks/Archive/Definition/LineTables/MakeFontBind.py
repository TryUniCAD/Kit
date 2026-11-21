from convert.adapters.solidworks.Archive.Definition.LineTables.FontBinding import (
    FontBinding,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# each new category receives a distinct font node and a preset width built by the native enum constructor
def MakeFontBind(InputValue: FontBinding) -> dict[str, object]:
    if type(InputValue) is not FontBinding:
        raise TypeError("line font construction requires typed semantic input")
    return {
        "key": InputValue.CategoryValue,
        "cfg": ArchiveNode(
            RuntimeClass("uiLFConfig_c", 1),
            {
                "f08": InputValue.FontName,
                "f10": {"f06": InputValue.WeightValue, "f00": -1.0},
                "f18": InputValue.EndCapValue,
            },
        ),
    }
