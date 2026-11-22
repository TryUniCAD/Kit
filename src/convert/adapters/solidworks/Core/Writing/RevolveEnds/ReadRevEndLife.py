from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# independent second angle edits add a measurement without replacing the first or the fresh reopen proof
def ReadRevEndLife(NativeCase: dict[str, object], SideValue: str) -> tuple[str, str]:
    Comparisons = ReadMeasMap(NativeCase.get("comparisons"))
    PhaseValue = NativeCase.get("native_phase_sha256")
    PhaseHashes = (
        CastValue(list[object], PhaseValue) if type(PhaseValue) is list else []
    )
    Needed = {"reopened", "edited", "edited_fresh_reopen"}
    if SideValue == "two_sided":
        Needed.add("after-d1")
    if (
        NativeCase.get("passed") is not True
        or NativeCase.get("native_phase_failures") != [None, None]
        or Comparisons.keys() != Needed
        or len(PhaseHashes) != 2
    ):
        raise ValueError("measured revolve ends require clean edits and fresh reopen")
    for Value in Comparisons.values():
        RowValue = ReadMeasMap(Value)
        if RowValue.get("mass_checks") != 6 or RowValue.get("tree_rows") != 19:
            raise ValueError(
                "measured revolve end comparison lacks mass or tree evidence"
            )
    return ReadMeasSha(PhaseHashes[0]), ReadMeasSha(PhaseHashes[1])
