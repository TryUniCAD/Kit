from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# reciprocal fins identify the actual two stock faces incident to a straight edge
def ReadFilletInc(
    NodesValue: Mapping[int, XmtNode], EdgeIndex: int
) -> tuple[XmtNode, XmtNode, frozenset[int]]:
    EdgeValue = RequireXmt(NodesValue, EdgeIndex, 16)
    FirstValue = RequireXmt(NodesValue, EdgeValue.Integer("halfedge"), 17)
    LastValue = RequireXmt(NodesValue, FirstValue.Integer("other"), 17)
    if (
        FirstValue is LastValue
        or FirstValue.Integer("edge") != EdgeIndex
        or LastValue.Integer("edge") != EdgeIndex
        or LastValue.Integer("other") != FirstValue.IndexValue
    ):
        raise ValueError("saved fillet stock has an inconsistent edge incidence")
    Faces = frozenset(
        RequireXmt(NodesValue, Value.Integer("loop"), 15).Integer("face")
        for Value in (FirstValue, LastValue)
    )
    return FirstValue, LastValue, Faces
