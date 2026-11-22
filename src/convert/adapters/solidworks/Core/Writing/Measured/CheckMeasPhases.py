from math import isclose as IsClose
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.MeasFields import (
    ReadMeasNum,
    ReadMeasRows,
    ReadMeasSha,
)


# exact native receipts bracket all measurements with the known passing control phases
def MeasPhaseMap(Receipt: dict[str, object]) -> dict[str, dict[str, object]]:
    PhaseRows = ReadMeasRows(Receipt.get("phases"))
    PhaseCount = Receipt.get("distinct_native_processes")
    if type(PhaseCount) is not int or PhaseCount != len(PhaseRows) or PhaseCount < 4:
        raise ValueError(
            "native measurement requires distinct fresh processes and both controls"
        )
    Reports: dict[str, dict[str, object]] = {}
    Digests: set[str] = set()
    for PhaseValue in PhaseRows:
        Label = PhaseValue.get("role")
        Digest = ReadMeasSha(PhaseValue.get("record_sha256"))
        CheckCount = PhaseValue.get("numeric_checks")
        if (
            type(Label) is not str
            or not Label
            or Label in Reports
            or Digest in Digests
            or PhaseValue.get("passed") is not True
            or type(CheckCount) is not int
            or CheckCount < 0
        ):
            raise ValueError("native measurement repeats or failed an oracle phase")
        Reports[Label] = PhaseValue
        Digests.add(Digest)
    Labels = tuple(Reports)
    if (Labels[0], Labels[-1]) != ("ControlBefore", "ControlAfter"):
        raise ValueError("native measurement phases must be bracketed by both controls")
    for Label in (Labels[0], Labels[-1]):
        Control = Reports[Label]
        if (
            Control.get("states") != []
            or Control.get("save_status") is not None
            or Control.get("derivative_sha256") is not None
        ):
            raise ValueError(
                "native measurement has the wrong model in a control phase"
            )
    TotalChecks = Receipt.get("numeric_checks")
    if type(TotalChecks) is not int or TotalChecks != sum(
        CastValue(int, Value["numeric_checks"]) for Value in PhaseRows
    ):
        raise ValueError("native measurement numerical coverage is inconsistent")
    return Reports


# recorded frame and solid measurements must be present for every accepted observation
def MeasState(
    StateValue: dict[str, object],
) -> tuple[int, tuple[float, ...]]:
    TreeCount = StateValue.get("rows")
    Center = StateValue.get("centre_of_mass_m")
    if (
        type(StateValue.get("bodies")) is not int
        or StateValue["bodies"] != 1
        or type(StateValue.get("warnings")) is not int
        or StateValue["warnings"] != 0
        or type(TreeCount) is not int
        or TreeCount < 1
        or type(Center) is not list
        or len(CastValue(list[object], Center)) != 3
        or any(
            not isinstance(Coord, (int, float))
            or isinstance(Coord, bool)
            or not -float("inf") < Coord < float("inf")
            for Coord in CastValue(list[object], Center)
        )
    ):
        raise ValueError(
            "native measurement has an incomplete or unclean solid observation"
        )
    return TreeCount, (
        ReadMeasNum(StateValue.get("depth_m")),
        ReadMeasNum(StateValue.get("volume_m3")),
        ReadMeasNum(StateValue.get("area_m2")),
        *(float(Coord) for Coord in CastValue(list[float], Center)),
    )


# the offline comparator allows native roundoff while retaining each observed body and driver
def IsSameMeasState(
    FirstValue: tuple[int, tuple[float, ...]],
    OtherValue: tuple[int, tuple[float, ...]],
) -> bool:
    return FirstValue[0] == OtherValue[0] and all(
        IsClose(First, Other, rel_tol=5e-7, abs_tol=(1e-11 if Index >= 3 else 0.0))
        for Index, (First, Other) in enumerate(
            zip(FirstValue[1], OtherValue[1], strict=True)
        )
    )


# a clean save must report exact success and separate zero error and warning counts
def IsCleanMeasSave(Value: object) -> bool:
    if type(Value) is not list:
        return False
    Items = CastValue(list[object], Value)
    return (
        len(Items) == 3
        and Items[0] is True
        and all(type(ItemValue) is int and ItemValue == 0 for ItemValue in Items[1:])
    )


# the matched candidate must have clean initial rebuild edit save and independently reopened gate rows
def CheckMeasSlot(
    Reports: dict[str, dict[str, object]],
    Label: str,
) -> tuple[str, str]:
    FirstName, ReopenName = Label + "Generated", Label + "Reopen"
    Edited, Reopen = Reports.get(FirstName), Reports.get(ReopenName)
    if (
        Edited is None
        or Reopen is None
        or tuple(Reports).index(FirstName) >= tuple(Reports).index(ReopenName)
    ):
        raise ValueError("native measurement lacks the matched candidate lifecycle")
    EditedRows, ReopenRows = ReadMeasRows(Edited.get("states"), 3), ReadMeasRows(
        Reopen.get("states"), 2
    )
    if (
        tuple(State.get("role") for State in EditedRows)
        != ("Initial", "Rebuilt", "Edited")
        or tuple(State.get("role") for State in ReopenRows) != ("Initial", "Rebuilt")
        or not IsCleanMeasSave(Edited.get("save_status"))
        or Reopen.get("save_status") is not None
        or Reopen.get("derivative_sha256") is not None
        or any(
            CastValue(int, Phase["numeric_checks"]) < 6 * len(States)
            for Phase, States in ((Edited, EditedRows), (Reopen, ReopenRows))
        )
    ):
        raise ValueError(
            "native measurement lacks clean measured edit save or fresh reopen evidence"
        )
    _ = ReadMeasSha(Edited.get("derivative_sha256"))
    Initial, Rebuilt, Changed, Reloaded, ReloadBuild = (
        MeasState(State) for State in (*EditedRows, *ReopenRows)
    )
    if (
        not IsSameMeasState(Initial, Rebuilt)
        or Initial[0] != Changed[0]
        or Initial[1][0] == Changed[1][0]
        or Initial[1][1] == Changed[1][1]
        or not IsSameMeasState(Changed, Reloaded)
        or not IsSameMeasState(Changed, ReloadBuild)
    ):
        raise ValueError(
            "native measurement does not preserve the edited solid and feature tree"
        )
    return ReadMeasSha(Edited.get("record_sha256")), ReadMeasSha(
        Reopen.get("record_sha256")
    )
