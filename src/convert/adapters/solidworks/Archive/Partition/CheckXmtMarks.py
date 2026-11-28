from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.History.CheckMarkChain import (
    CheckMarkChain,
)
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# existing body readers depend on a selected rollback that deletes the active body
def CheckXmtMarks(
    NodesValue: Mapping[int, XmtNode],
    RootValue: XmtNode,
    MarksValue: Mapping[int, XmtNode],
    DeletedSets: Mapping[int, frozenset[int]],
) -> None:
    Current = CheckMarkChain(NodesValue, RootValue, MarksValue, DeletedSets)
    BodyIndex = RequireXmt(NodesValue, 1, 101).Integer("body")
    if BodyIndex and BodyIndex not in DeletedSets.get(Current.IndexValue, frozenset()):
        raise ValueError("selected native rollback does not own the active body")
