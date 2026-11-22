from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.CylJournal import (
    CylJournal,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeImportMarks import (
    KFirstDeltaKey,
    KFirstMarkId,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# a retained rollback mark links the chronological predecessors and counts hidden pointer allocations
def MakeCylMark(
    IndexValue: int,
    PriorValue: int,
    NextValue: int,
    MarkId: int,
    DeltaKey: int,
    NewCount: int = 0,
) -> XmtNode:
    return XmtNode(
        IndexValue,
        4,
        {
            "preceding": PriorValue,
            "first_following": NextValue,
            "next_sibling": 0,
            "prev_sibling": 0,
            "delta_key": DeltaKey,
            "delta_is_forward": 0,
            "id": MarkId,
            "n_new_nodes": NewCount,
            "n_del_nodes": 0,
            "n_copy_mod_nodes": 0,
        },
    )


# fresh attachment allocates activation and an intervening discarded mark before geometry
def MakeCylMarks(
    ActiveValue: tuple[XmtNode, ...],
    HiddenCount: int,
) -> CylJournal:
    RootIndex = len(ActiveValue) + 1
    SelectedIndex, ActivationIndex, InitialIndex = range(RootIndex + 1, RootIndex + 4)
    EventsValue = ("activation", "intervening", "geometry")
    SelectedId = KFirstMarkId + len(EventsValue)
    Removed = tuple(
        NodeValue
        for NodeValue in reversed(ActiveValue)
        if NodeValue.KindValue not in (101, 79, 80)
    )
    RootValue = XmtNode(
        RootIndex,
        3,
        {
            "current_pmark": SelectedIndex,
            "highest_id": SelectedId,
        },
    )
    return CylJournal(
        RootValue,
        MakeCylMark(
            SelectedIndex,
            ActivationIndex,
            0,
            SelectedId,
            KFirstDeltaKey + EventsValue.index("geometry"),
            len(Removed) + HiddenCount,
        ),
        MakeCylMark(InitialIndex, 0, ActivationIndex, KFirstMarkId, 0),
        MakeCylMark(
            ActivationIndex,
            InitialIndex,
            SelectedIndex,
            KFirstMarkId + 1,
            KFirstDeltaKey,
        ),
        Removed,
    )
