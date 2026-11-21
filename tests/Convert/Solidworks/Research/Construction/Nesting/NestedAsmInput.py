from ntpath import join as JoinPath
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmInput import (
    MakeAsmInput,
)


# every generated assembly definition needs its own authored output identity while sharing the same classified native system and provenance contract
def NestedAsmInput(NameValue: str, OutputRoot: str) -> dict[str, object]:
    InputValue = CastValue(
        dict[str, object], MakeAsmInput(NameValue, False)["assembly"]
    )
    OutputValue = CastValue(dict[str, object], InputValue["output"])
    OutputValue["path_name"] = JoinPath(OutputRoot, NameValue + ".SLDASM")
    Definition = CastValue(dict[str, object], InputValue["definition"])
    Definition["journal_name"] = NameValue
    return InputValue
