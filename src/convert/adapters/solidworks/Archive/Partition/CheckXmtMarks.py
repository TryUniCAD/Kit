from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences


# native selected history must identify the active world without ambiguous marks or rollbacks
def CheckXmtMarks(
    NodesValue: Mapping[int, XmtNode],
    RootValue: XmtNode,
    MarksValue: Mapping[int, XmtNode],
    DeletedSets: Mapping[int, frozenset[int]],
) -> None:
    WorldValue = RequireXmt(NodesValue, 1, 101)
    Current = RequireXmt(MarksValue, RootValue.Integer("current_pmark"), 4)
    MarkIds = {MarkValue.Integer("id") for MarkValue in MarksValue.values()}
    if (
        not MarksValue
        or len(MarkIds) != len(MarksValue)
        or min(MarkIds) != 1
        or RootValue.IndexValue in NodesValue
        or RootValue.IndexValue in MarksValue
        or WorldValue.Integer("current_id") != Current.Integer("id")
        or WorldValue.Integer("highest_id") != RootValue.Integer("highest_id")
        or max(MarkIds) > RootValue.Integer("highest_id")
    ):
        raise ValueError("native world and history identities disagree")
    DeltaKeys: set[int] = set()
    for MarkValue in MarksValue.values():
        if (
            any(IndexValue not in MarksValue for IndexValue in XmtReferences(MarkValue))
            or MarkValue.Integer("delta_is_forward")
            or MarkValue.Integer("next_sibling")
            or MarkValue.Integer("prev_sibling")
        ):
            raise ValueError(
                "native history is not the witnessed linear rollback profile"
            )
        PriorValue = MarkValue.Integer("preceding")
        Following = MarkValue.Integer("first_following")
        if PriorValue:
            PriorMark = MarksValue[PriorValue]
            if PriorMark.Integer(
                "first_following"
            ) != MarkValue.IndexValue or PriorMark.Integer("id") >= MarkValue.Integer(
                "id"
            ):
                raise ValueError("native history predecessor is inconsistent")
        if (
            Following
            and MarksValue[Following].Integer("preceding") != MarkValue.IndexValue
        ):
            raise ValueError("native history successor is inconsistent")
        DeltaKey = MarkValue.Integer("delta_key")
        if not DeltaKey:
            if (
                MarkValue.Integer("id") != 1
                or PriorValue
                or MarkValue.IndexValue in DeletedSets
            ):
                raise ValueError("native initial mark has unqualified rollback state")
        elif (
            DeltaKey < 0
            or DeltaKey in DeltaKeys
            or not PriorValue
            or MarkValue.IndexValue not in DeletedSets
        ):
            raise ValueError(
                "native rollback does not have a unique retained predecessor"
            )
        DeltaKeys.add(DeltaKey)
    BodyIndex = WorldValue.Integer("body")
    if BodyIndex and BodyIndex not in DeletedSets.get(Current.IndexValue, frozenset()):
        raise ValueError("selected native rollback does not own the active body")
