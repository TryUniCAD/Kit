from tests.Convert.Solidworks.Research.Construction.Part.AssertPartFlow import (
    AssertPartFlow,
)
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)
from tests.Convert.Solidworks.Research.Construction.Part.RunPartPhase import (
    RunPartPhase,
)


# two independently authored neutral parts must build and prepare complete native streams with input dependent geometry names lengths and aliases
def TestBlindPart() -> None:
    LengthValues: list[int] = []
    for NameValue, IsVariant in (
        ("sdk plain alpha", False),
        ("sdk 部品 plain beta extended", True),
    ):
        InputValue = BlindCaseInput(NameValue, IsVariant)
        BuildValue = RunPartPhase(InputValue, "build")
        Request: dict[str, object] = {"request": InputValue, "build": BuildValue}
        Prepared = RunPartPhase(Request, "prepare")
        Counterpart = RunPartPhase(Request, "counterpart")
        LengthValues.append(AssertPartFlow(BuildValue, Prepared, Counterpart))
    assert LengthValues[0] != LengthValues[1]
