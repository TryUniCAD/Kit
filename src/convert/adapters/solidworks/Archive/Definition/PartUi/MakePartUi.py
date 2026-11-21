from convert.adapters.solidworks.Archive.Definition.PartUi.PartUiInput import (
    PartUiInput,
)


# native part context confirmation determines kind while documented view and toolbar choices determine saved operands
def MakePartUi(InputValue: PartUiInput) -> dict[str, object]:
    if type(InputValue) is not PartUiInput:
        raise TypeError("part ui construction requires typed view and toolbar input")
    return {
        "fad0": InputValue.HlrQualityCode,
        "fad4": 2 | int(InputValue.DisplayGrid),
        "fb00": 1,
        "fb04": 0x958C if InputValue.DefaultCommandGroup == "features" else 0,
    }
