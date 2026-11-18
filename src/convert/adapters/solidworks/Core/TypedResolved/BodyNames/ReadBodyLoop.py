from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# exact fin ownership prevents a matching label from qualifying detached or incomplete geometry
def ReadBodyLoop(
    NodesValue: Mapping[int, XmtNode], FaceValue: XmtNode
) -> tuple[int, tuple[int, ...]]:
    LoopValue = RequireXmt(NodesValue, FaceValue.Integer("loop"), 15)
    if LoopValue.Integer("face") != FaceValue.IndexValue or LoopValue.Integer("next"):
        raise ValueError("named face has unqualified trimming")
    FirstIndex = LoopValue.Integer("halfedge")
    IndexValue = FirstIndex
    FinIds: list[int] = []
    while len(FinIds) < 4:
        if IndexValue in FinIds:
            raise ValueError("named face fin ring closes prematurely")
        FinValue = RequireXmt(NodesValue, IndexValue, 17)
        MateValue = RequireXmt(NodesValue, FinValue.Integer("other"), 17)
        NextValue = RequireXmt(NodesValue, FinValue.Integer("forward"), 17)
        if (
            FinValue.Integer("loop") != LoopValue.IndexValue
            or MateValue.Integer("other") != IndexValue
            or MateValue.Integer("edge") != FinValue.Integer("edge")
            or MateValue.String("sense") == FinValue.String("sense")
            or NextValue.Integer("backward") != IndexValue
            or FinValue.Integer("vertex")
            != RequireXmt(NodesValue, NextValue.Integer("other"), 17).Integer("vertex")
        ):
            raise ValueError("named solid fin ownership is inconsistent")
        FinIds.append(IndexValue)
        IndexValue = FinValue.Integer("forward")
    if IndexValue != FirstIndex:
        raise ValueError("named face fin ring is not closed")
    return LoopValue.IndexValue, tuple(FinIds)
