from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# local fin links must agree across both uses of each solid edge
def CheckLocalFins(NodesValue: Mapping[int, XmtNode], FinValue: XmtNode) -> None:
    MateValue = RequireXmt(NodesValue, FinValue.Integer("other"), 17)
    NextValue = RequireXmt(NodesValue, FinValue.Integer("forward"), 17)
    if (
        MateValue.Integer("other") != FinValue.IndexValue
        or MateValue.Integer("edge") != FinValue.Integer("edge")
        or MateValue.Integer("loop") == FinValue.Integer("loop")
        or {MateValue.String("sense"), FinValue.String("sense")} != {"+", "-"}
        or NextValue.Integer("backward") != FinValue.IndexValue
        or NextValue.Integer("loop") != FinValue.Integer("loop")
        or RequireXmt(NodesValue, NextValue.Integer("other"), 17).Integer("vertex")
        != FinValue.Integer("vertex")
    ):
        raise ValueError("local body has inconsistent fin ownership")
