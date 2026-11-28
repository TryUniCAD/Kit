from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)


# reached classes must be confined to the single selected physical solid
def XmtKindIds(NodesValue: Mapping[int, XmtNode], KindValue: int) -> set[int]:
    return {
        NodeValue.IndexValue
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == KindValue
    }


# a closed sweep result has no unowned resident records outside its current world
def CheckSwReach(NodesValue: Mapping[int, XmtNode], WorldValue: XmtNode) -> None:
    SeenValue: set[int] = set()
    Pending = {WorldValue.IndexValue}
    while Pending:
        IndexValue = Pending.pop()
        SeenValue.add(IndexValue)
        Pending.update(
            RefValue
            for RefValue in XmtReferences(NodesValue[IndexValue])
            if RefValue not in SeenValue
        )
    if SeenValue != set(NodesValue):
        raise ValueError("SOLIDWORKS saved sweep contains a detached resident result")


# the actual both sided solid inventory must bind before a geometric result can be projected
def ReadSwShell(
    NodesValue: Mapping[int, XmtNode],
) -> tuple[XmtNode, tuple[XmtNode, ...]]:
    CheckXmtGraph(NodesValue)
    WorldValue = RequireXmt(NodesValue, 1, 101)
    BodyValue = RequireXmt(NodesValue, WorldValue.Integer("body"), 12)
    ShellValue = RequireXmt(NodesValue, BodyValue.Integer("shell"), 13)
    if ShellValue.Integer("next"):
        raise ValueError("SOLIDWORKS saved sweep solid shell has a sibling link")
    FaceIds = ReadBodyFaces(NodesValue, BodyValue, 3)
    if (
        XmtKindIds(NodesValue, 12) != {BodyValue.IndexValue}
        or XmtKindIds(NodesValue, 14) != set(FaceIds)
        or XmtKindIds(NodesValue, 18)
        or XmtKindIds(NodesValue, 29)
        or BodyValue.Integer("owner") != WorldValue.IndexValue
        or BodyValue.Integer("body_type") != 1
        or BodyValue.Integer("next")
        or BodyValue.Integer("previous")
        or BodyValue.Integer("vertex")
        or BodyValue.Integer("boundary_point")
    ):
        raise ValueError("SOLIDWORKS saved sweep lacks its sole closed physical shell")
    CheckSwReach(NodesValue, WorldValue)
    return BodyValue, tuple(NodesValue[IndexValue] for IndexValue in FaceIds)
