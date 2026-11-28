from math import isclose as IsClose
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Core.Writing.Ellipse.CheckEllipMass import (
    CheckEllipMass,
)
from convert.adapters.solidworks.Core.Writing.Ellipse.CheckEllipState import (
    CheckEllipState,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows


# complete open edit save and reopen evidence must preserve the edited depth and measured solid
def CheckEllipEdits(CaseValue: dict[str, object], PlanValue: EllipsePlan) -> None:
    States = ReadMeasRows(CaseValue.get("states"), 3)
    SaveStatus = CaseValue.get("save_status")
    Loader = CaseValue.get("opens")
    if (
        tuple(State.get("stage") for State in States) != ("initial", "edited", "reopen")
        or type(SaveStatus) is not list
        or len(CastValue(list[object], SaveStatus)) != 3
        or CastValue(list[object], SaveStatus)[0] is not True
        or any(
            type(Value) is not int or Value != 0
            for Value in CastValue(list[object], SaveStatus)[1:]
        )
        or Loader != [[0, 0], [0, 0]]
        or type(CaseValue.get("setter_status")) is not int
        or CaseValue["setter_status"] != 0
    ):
        raise ValueError("ellipse measurement lacks clean native edit save or reopen")
    Initial, Edited, Reopened = (CheckEllipState(StateValue) for StateValue in States)
    if not IsClose(Initial[0], PlanValue.DepthValue, rel_tol=1e-14):
        raise ValueError(
            "ellipse measurement does not match the generated driving depth"
        )
    if (
        Initial[0] == Edited[0]
        or Initial[1] == Edited[1]
        or not all(
            IsClose(First, Other, rel_tol=5e-7, abs_tol=(1e-11 if Index >= 3 else 0.0))
            for Index, (First, Other) in enumerate(zip(Edited, Reopened, strict=True))
        )
    ):
        raise ValueError(
            "ellipse measurement does not preserve the edited depth and body"
        )
    CheckEllipMass(PlanValue, Initial, PlanValue.DepthValue)
    for StateValue in (Edited, Reopened):
        CheckEllipMass(PlanValue, StateValue, StateValue[0])
