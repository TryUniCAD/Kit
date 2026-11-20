from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the local import may carry the concrete empty configuration manager without adding resolved history
def ReadLocalExpl(LinkValue: NativeLink) -> ArchiveNode | None:
    RootValue = LinkValue.ConfigValue.RootValue
    FieldValue = RootValue.FieldsValue.get("f13f8")
    if FieldValue is None:
        return None
    NodeValue = RequireNative(FieldValue, "moPrtExplViewManager_c")
    ClassValue = NodeValue.ClassValue
    FieldsValue = NodeValue.FieldsValue
    EmptyRows = {"n": 0, "items": list[object]()}
    if (
        not isinstance(ClassValue, RuntimeClass)
        or ClassValue.SchemaValue != 1
        or NativeNodeId(NodeValue) == 0
        or RootValue.FieldsValue.get("f1400") != 0
        or type(FieldsValue.get("f398")) is not float
        or any(
            NameValue not in FieldsValue or FieldsValue[NameValue] != DefaultValue
            for NameValue, DefaultValue in (
                ("f18", None),
                ("f358", None),
                ("f360", None),
                ("f368", EmptyRows),
                ("f398", 0.0),
                ("f3a0", -1),
                ("f3a4", -1),
                ("f60", {"list": EmptyRows, "tail": 0}),
            )
        )
        or NativeNodeSpan(LinkValue, NodeValue)["stream"] != LinkValue.ConfigName
        or any(NodeValue is RootItem for RootItem in LinkValue.ResolvedValue.RootsValue)
    ):
        raise ValueError("local import has unsupported exploded view state")
    CheckTreeAlias(LinkValue, (NodeValue,))
    return NodeValue
