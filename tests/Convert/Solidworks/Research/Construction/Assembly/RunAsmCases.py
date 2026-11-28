from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import (
    MakeAsmCase,
)
from tests.Convert.Solidworks.Research.Construction.Assembly.RunAsmPhase import (
    RunAsmPhase,
)


# all principal axes and unrelated plain child variants must preserve complete native graph aliases and independently generated stream bytes for each mate family
def RunAsmCases(KindValue: str) -> None:
    LengthValues: list[int] = []
    for AxisValue in "xyz":
        for IsVariant in (False, True):
            Request = MakeAsmCase(KindValue, AxisValue, IsVariant)
            BuildValue = RunAsmPhase(Request, "build")
            Projected: dict[str, object] = {"request": Request, "build": BuildValue}
            Prepared = RunAsmPhase(Projected, "prepare")
            Counterpart = RunAsmPhase(Projected, "counterpart")
            assert Prepared["round_trips"] == 22
            assert Counterpart["same_as_independent_research"] is True
            assert (
                BuildValue["actual_child_identity"]
                is BuildValue["child_bytes_unchanged"]
                is True
            )
            ChildValue = CastValue(dict[str, object], BuildValue["child"])
            LengthValues.append(CastValue(int, ChildValue["bytes"]))
    assert len(set(LengthValues)) == 2
