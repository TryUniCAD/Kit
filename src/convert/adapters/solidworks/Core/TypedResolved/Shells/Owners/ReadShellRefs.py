from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    ChmfRoleKey,
    ReadChmfRef,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Shells.Owners.CheckShellFile import (
    CheckShellFile,
)


# component references must alias the local part and selected configuration atom
def ReadShellComp(
    LinkValue: NativeLink, NodeValue: ArchiveNode, AtomId: object, IsFace: bool
) -> ArchiveNode:
    Fields = NodeValue.FieldsValue
    Component = RequireNative(Fields.get("f58"), "moUnitComponent_c")
    if (
        Component.FieldsValue.get("owner") is not LinkValue.ConfigValue.RootValue
        or Component.FieldsValue.get("has_ext") != 0
        or Fields.get("f18") != AtomId
        or Fields.get("f1c") != AtomId
        or Fields.get("has_alias") != 0
        or Fields.get("ff0") is not None
    ):
        raise ValueError(
            "SOLIDWORKS shell selection has another component or atom owner"
        )
    RefValue = RequireNative(
        Fields.get("fe8"), "moFaceRef_c" if IsFace else "moEdgeRef_c"
    )
    CheckTreeAlias(LinkValue, (NodeValue, Component, RefValue))
    return RefValue


# the selected physical reference checks its own representation count and stored local producer
def ReadShellRefs(
    LinkValue: NativeLink,
    RefValue: ArchiveNode,
    StockNode: ArchiveNode,
    TopHeader: ArchiveNode,
    *,
    IsFace: bool,
) -> tuple[tuple[object, ...], ...]:
    Fields = RefValue.FieldsValue
    RowsValue = NativeRows(Fields.get("f10"))
    if (
        Fields.get("f08") != len(RowsValue)
        or Fields.get("fe8") != (768 if IsFace else 512)
        or Fields.get("f60") != 1
        or Fields.get("f64") != 0
        or Fields.get("has_f18") != 0
        or Fields.get("f40") is not None
        or Fields.get("nd0") != 0
        or (IsFace and Fields.get("nf0") != 0)
    ):
        raise ValueError(
            "SOLIDWORKS shell geometry carries an unsupported reference mode"
        )
    Records = tuple(RowValue.get("f08") for RowValue in RowsValue)
    if IsFace and (len(Records) != 6 or Records[-1] is not None):
        raise ValueError("SOLIDWORKS shell cap has alternative reference carriers")
    Nodes = tuple(
        RequireNative(Value) for Value in (Records[:-1] if IsFace else Records)
    )
    Files = {
        RequireNative(
            ReadChmfRef(LinkValue, Value, StockNode, TopHeader, False).FieldsValue.get(
                "f08"
            ),
            "moExtObject_c",
        )
        for Value in Nodes
    }
    (FileValue,) = Files
    CheckShellFile(FileValue, LinkValue.ConfigValue.HeaderValue, TopHeader)
    CheckTreeAlias(LinkValue, (FileValue,))
    return tuple(ChmfRoleKey(Value) for Value in Nodes)
