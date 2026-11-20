from convert.adapters.solidworks.Archive.Partition.CheckXmtMarks import CheckXmtMarks
from convert.adapters.solidworks.Archive.Partition.ImportHistory.ImportEvent import (
    ImportEvent,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.ImportHistory import (
    ImportHistory,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeEmptyWorld import (
    MakeEmptyWorld,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeImportMarks import (
    MakeImportMarks,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.WriteImportHist import (
    WriteImportHist,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# fresh local imports need an empty active partition and exact marks for both native owners
def MakeImportHist(
    VersionValue: int, EventValues: tuple[ImportEvent, ...]
) -> ImportHistory:
    if (
        type(VersionValue) is not int
        or VersionValue != 19000
        or type(EventValues) is not tuple
        or len(EventValues) != 2
        or any(type(EventValue) is not ImportEvent for EventValue in EventValues)
        or EventValues != (ImportEvent.KActivation, ImportEvent.KLocalAttach)
    ):
        raise ValueError(
            "import history needs fresh 2026 activation and local body attachment"
        )
    WorldIndex = 1
    RootIndex = WorldIndex + 1
    InitialMark, Activation, Selected = MakeImportMarks(RootIndex, len(EventValues))
    SelectedId = Selected.Integer("id")
    WorldValue = MakeEmptyWorld(WorldIndex, 1, SelectedId)
    RootValue = XmtNode(
        RootIndex, 3, {"current_pmark": Selected.IndexValue, "highest_id": SelectedId}
    )
    MarksValue = (Selected, InitialMark, Activation)
    CheckXmtMarks(
        {WorldIndex: WorldValue},
        RootValue,
        {MarkValue.IndexValue: MarkValue for MarkValue in MarksValue},
        {Activation.IndexValue: frozenset(), Selected.IndexValue: frozenset()},
    )
    return ImportHistory(
        WriteImportHist(WorldValue, RootValue, MarksValue),
        (Activation.Integer("id"), SelectedId),
    )
