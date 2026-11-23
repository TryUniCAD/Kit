from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# each recess corner needs one closed rotation through its three terminal fins
def CheckPocketFins(NodesValue: Mapping[int, XmtNode]) -> None:
    UsedValue: set[int] = set()
    for VertexValue in NodesValue.values():
        if VertexValue.KindValue != 18:
            continue
        FinIds = WalkXmtChain(
            NodesValue,
            VertexValue.Integer("halfedge"),
            17,
            "next_at_vx",
            None,
            "vertex",
            VertexValue.IndexValue,
        )
        Rotation = tuple(
            RequireXmt(
                NodesValue, NodesValue[IndexValue].Integer("forward"), 17
            ).Integer("other")
            for IndexValue in FinIds
        )
        if len(FinIds) != 3 or Rotation != FinIds[1:] + FinIds[:1]:
            raise ValueError("local pocket vertex has inconsistent fin rotation")
        UsedValue.update(FinIds)
    if UsedValue != {
        Value.IndexValue for Value in NodesValue.values() if Value.KindValue == 17
    }:
        raise ValueError("local pocket vertex chains do not own all fins")
