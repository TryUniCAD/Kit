from math import isclose as IsClose
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepPart import SweepPart
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Sweeps.CheckSwState import CheckSwState
from convert.adapters.solidworks.Core.Writing.Sweeps.HasCleanSwCode import (
    HasCleanSwCode,
)


# each saved edit must persist its own editable dimension and measured body without changing the other dimension
def CheckSwEdits(CaseValue: dict[str, object], Candidate: SweepPart) -> None:
    States = ReadMeasRows(CaseValue.get("states"), 5)
    Saves = CaseValue.get("save_status")
    if (
        tuple(Value.get("stage") for Value in States)
        != ("initial", "section-edited", "section-reopen", "path-edited", "path-reopen")
        or type(Saves) is not list
        or len(CastValue(list[object], Saves)) != 2
        or not all(
            HasCleanSwCode(Value, SaveFlag=True)
            for Value in CastValue(list[object], Saves)
        )
        or not HasCleanSwCode(CaseValue.get("setter_status"))
        or CaseValue.get("paired_numeric_checks") != 84
    ):
        raise ValueError(
            "sweep measurement lacks clean native driver edits or numeric coverage"
        )
    Initial, *Edits = (CheckSwState(Value) for Value in States)
    Profiles = Candidate.ProfilesValue
    DiamValue = RequireScalar(Profiles.DiameterValue.ParameterValue.FieldsValue["f58"])
    Radius = RequireScalar(Profiles.RadiusValue.ParameterValue.FieldsValue["f58"])
    if not all(
        IsClose(Value, Actual, rel_tol=1e-14)
        for Value, Actual in zip(Initial[:2], (DiamValue, Radius), strict=True)
    ):
        raise ValueError(
            "sweep measurement does not match both generated driving dimensions"
        )
    for Index, (Edited, Reopen) in enumerate((Edits[:2], Edits[2:])):
        if (
            Initial[Index] == Edited[Index]
            or Initial[1 - Index] != Edited[1 - Index]
            or Initial[2] == Edited[2]
            or Edited[:2] != Reopen[:2]
            or any(
                not IsClose(
                    Value,
                    Actual,
                    rel_tol=5e-7,
                    abs_tol=1e-11 if FieldIndex >= 5 else 0.0,
                )
                for FieldIndex, (Value, Actual) in enumerate(
                    zip(Edited[2:], Reopen[2:], strict=True), 2
                )
            )
        ):
            raise ValueError(
                "sweep measurement does not preserve the isolated edits and reopened body"
            )
