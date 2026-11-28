from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Ellipse.CheckEllipEdits import (
    CheckEllipEdits,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# the original and saved derivative hashes join the corresponding native lifetimes for this one case
def CheckEllipSlot(
    Phases: tuple[dict[str, object], ...],
    CaseValue: dict[str, object],
    DepthValue: float,
) -> tuple[str, str]:
    SlotId = CaseValue["slot"]
    Matches = tuple(
        Value
        for Value in Phases
        if type(Value.get("slot")) is int and Value["slot"] == SlotId
    )
    if len(Matches) != 2:
        raise ValueError(
            "ellipse measurement lacks the matched edit and reopen lifetimes"
        )
    EditPhase, Reopen = Matches
    if (
        (EditPhase.get("phase"), Reopen.get("phase")) != ("edit", "reopen")
        or EditPhase.get("source") != CaseValue["archive_sha256"]
        or Reopen.get("source") != ReadMeasSha(CaseValue.get("edited_sha256"))
        or any(
            Value.get("control") is not None or CastValue(int, Value["checks"]) < 18
            for Value in Matches
        )
    ):
        raise ValueError(
            "ellipse measurement does not bind the exact native edit and saved reopen"
        )
    CheckEllipEdits(CaseValue, DepthValue)
    return ReadMeasSha(EditPhase["receipt_sha256"]), ReadMeasSha(
        Reopen["receipt_sha256"]
    )
