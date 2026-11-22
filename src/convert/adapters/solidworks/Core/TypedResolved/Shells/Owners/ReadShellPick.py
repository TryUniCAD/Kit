from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Shells.Owners.CheckShellChsr import (
    CheckShellChsr,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Owners.ReadShellRefs import (
    ReadShellComp,
    ReadShellRefs,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ShellStock import (
    ShellStock,
)


# one selected top cap owns removal while the detached edge only corroborates history
def ReadShellPick(
    LinkValue: NativeLink,
    ShellNode: ArchiveNode,
    Stock: ShellStock,
    AtomNode: ArchiveNode,
    TopHeader: ArchiveNode,
) -> ArchiveNode:
    Fields = ShellNode.FieldsValue
    Picks = RequireNative(Fields.get("f828"), "suObList").FieldsValue
    if (
        Fields.get("f820") != 0
        or Fields.get("f850") is not None
        or not all(IsLineState(Fields.get(NameValue)) for NameValue in ("f830", "f838"))
        or Picks.get("n") != 1
    ):
        raise ValueError(
            "SOLIDWORKS shell requires one selected cap and uniform inward thickness"
        )
    (RowValue,) = NativeRows(Picks.get("items"))
    AtomId = AtomNode.FieldsValue["f140"]
    FaceValue = RequireNative(RowValue.get("o"), "moCompFace_c")
    EdgeValue = RequireNative(Fields.get("f848"), "moCompEdge_c")
    StockNode = Stock.OwnerValue.NodeValue
    TopRef = ReadShellComp(LinkValue, FaceValue, AtomId, True)
    EdgeRef = ReadShellComp(LinkValue, EdgeValue, AtomId, False)
    TopKeys = ReadShellRefs(LinkValue, TopRef, StockNode, TopHeader, IsFace=True)
    EdgeKeys = ReadShellRefs(LinkValue, EdgeRef, StockNode, TopHeader, IsFace=False)
    Sides = {
        ("moFromSktEntSurfIdRep_c", Value.PermanentId, None)
        for Value in Stock.LoopValue.LinesValue
    }
    if (
        TopKeys[0] != ("moEndFaceSurfIdRep_c", 1, 0)
        or set(TopKeys[1:]) != Sides
        or len(EdgeKeys) != 4
        or len(set(EdgeKeys) & Sides) != 3
        or set(EdgeKeys) - Sides != {("moEndFaceSurfIdRep_c", 0, 0)}
    ):
        raise ValueError(
            "SOLIDWORKS shell removed face is outside the actual stock cap profile"
        )
    CheckShellChsr(LinkValue, StockNode, TopHeader, TopKeys)
    return TopRef
