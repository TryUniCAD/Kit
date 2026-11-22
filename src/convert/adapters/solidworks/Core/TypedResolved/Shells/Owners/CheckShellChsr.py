from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Shells.Owners.ReadShellRefs import (
    ReadShellRefs,
)


# chooser data must contain the two actual caps over the same rectangular stock
def CheckShellChsr(
    LinkValue: NativeLink,
    StockNode: ArchiveNode,
    TopHeader: ArchiveNode,
    TopKeys: tuple[tuple[object, ...], ...],
) -> None:
    for FieldName in ("f4a8", "f4b0", "f4c0"):
        Chooser = NativeRecord(StockNode.FieldsValue.get(FieldName))
        Embedded = NativeRecord(Chooser.get("f48"))
        RowsValue = NativeRows(Embedded.get("items"))
        CountValue = int(FieldName != "f4b0")
        if (
            Chooser.get("f68") is not StockNode
            or Embedded.get("n") != CountValue
            or len(RowsValue) != CountValue
        ):
            raise ValueError("SOLIDWORKS shell stock chooser has a different owner")
        for RowValue in RowsValue:
            NodeValue = RequireNative(RowValue.get("o"), "moPerBodyChooserData_c")
            CheckOwnedCaps(LinkValue, StockNode, TopHeader, TopKeys, NodeValue)


# saved choose lists prove that the occupied cap role belongs to the earlier extrusion
def CheckOwnedCaps(
    LinkValue: NativeLink,
    StockNode: ArchiveNode,
    TopHeader: ArchiveNode,
    TopKeys: tuple[tuple[object, ...], ...],
    NodeValue: ArchiveNode,
) -> None:
    ListValue = NativeRecord(NodeValue.FieldsValue.get("f08"))
    Bottom, Upper = (
        RequireNative(RowValue.get("o"), "moFaceRef_c")
        for RowValue in NativeRows(ListValue.get("items"))
    )
    CheckTreeAlias(LinkValue, (NodeValue, Bottom, Upper))
    BottomKeys, UpperKeys = (
        ReadShellRefs(LinkValue, RefValue, StockNode, TopHeader, IsFace=True)[0]
        for RefValue in (Bottom, Upper)
    )
    if (
        ListValue.get("n") != 2
        or len({Bottom, Upper}) != 2
        or UpperKeys != TopKeys
        or BottomKeys[0] != ("moEndFaceSurfIdRep_c", 0, 0)
        or set(BottomKeys[1:]) != set(TopKeys[1:])
    ):
        raise ValueError("SOLIDWORKS shell stock chooser does not own both cap roles")
