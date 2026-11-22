from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha

from convert.adapters.solidworks.Core.Writing.Sweeps.HasCleanSwCode import (
    HasCleanSwCode,
)
from convert.adapters.solidworks.Core.Writing.Sweeps.SweepMeasPhases import (
    KSwMeasPhases,
)


# original and derivative hashes link both independent edits to their clean saved reopens
def CheckSwPhases(
    Phases: tuple[dict[str, object], ...], CaseValue: dict[str, object]
) -> tuple[str, ...]:
    SlotValue = CastValue(int, CaseValue["slot"])
    PhaseCount = len(KSwMeasPhases)
    Selected = Phases[SlotValue * PhaseCount : (SlotValue + 1) * PhaseCount]
    NativeHash = ReadMeasSha(CaseValue["archive_sha256"])
    SectionHash = ReadMeasSha(CaseValue.get("section_save_sha256"))
    PathHash = ReadMeasSha(CaseValue.get("path_save_sha256"))
    if (
        len({NativeHash, SectionHash, PathHash}) != 3
        or tuple(Value.get("phase") for Value in Selected) != KSwMeasPhases
        or tuple(Value.get("source") for Value in Selected)
        != (NativeHash, NativeHash, SectionHash, NativeHash, PathHash)
        or tuple(Value.get("result") for Value in Selected)
        != (NativeHash, SectionHash, SectionHash, PathHash, PathHash)
        or any(
            type(Value.get("slot")) is not int
            or Value["slot"] != SlotValue
            or not HasCleanSwCode(Value.get("open_status"))
            or Value.get("rebuilt") is not True
            or CastValue(int, Value["checks"]) < 12
            for Value in Selected
        )
    ):
        raise ValueError(
            "sweep measurement does not bind the exact native edits and saved reopens"
        )
    return tuple(ReadMeasSha(Value["receipt_sha256"]) for Value in Selected)
