from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# full rings and partial sectors must exhaust their actual loop and reciprocal fin owners
def ReadRevLoops(
    NodesValue: Mapping[int, XmtNode], FaceValue: XmtNode, IsFull: bool
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    LoopIds = WalkXmtChain(
        NodesValue,
        FaceValue.Integer("loop"),
        15,
        PreviousField=None,
        OwnerField="face",
        OwnerValue=FaceValue.IndexValue,
    )
    if len(LoopIds) != (2 if IsFull else 1):
        raise ValueError("revolve face has unqualified trimming loops")
    FinIds: list[int] = []
    for LoopIndex in LoopIds:
        FirstIndex = NodesValue[LoopIndex].Integer("halfedge")
        IndexValue = FirstIndex
        RingIds: list[int] = []
        for _ in range(1 if IsFull else 4):
            if IndexValue in RingIds or IndexValue in FinIds:
                raise ValueError("revolve fin ring closes before its actual boundary")
            FinValue = RequireXmt(NodesValue, IndexValue, 17)
            MateValue = RequireXmt(NodesValue, FinValue.Integer("other"), 17)
            NextValue = RequireXmt(NodesValue, FinValue.Integer("forward"), 17)
            if (
                FinValue.Integer("loop") != LoopIndex
                or MateValue.Integer("other") != IndexValue
                or MateValue.Integer("edge") != FinValue.Integer("edge")
                or MateValue.String("sense") == FinValue.String("sense")
                or NextValue.Integer("backward") != IndexValue
                or FinValue.Integer("vertex")
                != RequireXmt(NodesValue, NextValue.Integer("other"), 17).Integer(
                    "vertex"
                )
                or (FinValue.Integer("vertex") == 0) != IsFull
            ):
                raise ValueError(
                    "revolve fin topology has foreign or mismatched ownership"
                )
            RingIds.append(IndexValue)
            IndexValue = FinValue.Integer("forward")
        if IndexValue != FirstIndex:
            raise ValueError("revolve fin ring is not completely closed")
        FinIds.extend(RingIds)
    return LoopIds, tuple(FinIds)
