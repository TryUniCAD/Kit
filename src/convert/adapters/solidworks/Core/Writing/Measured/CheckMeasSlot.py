from typing import cast as CastValue
from convert.adapters.solidworks.Core.Writing.Measured.IsCleanMeasSave import (
    IsCleanMeasSave,
)
from convert.adapters.solidworks.Core.Writing.Measured.IsSameMeasState import (
    IsSameMeasState,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasState import MeasState
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


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
