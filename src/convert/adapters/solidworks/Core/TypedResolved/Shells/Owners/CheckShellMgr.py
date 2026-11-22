from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the separate manager must corroborate the same atom and both persistent feature identities
def CheckShellMgr(
    LinkValue: NativeLink,
    StockNode: ArchiveNode,
    ShellNode: ArchiveNode,
    AtomNode: ArchiveNode,
) -> None:
    Manager = LinkValue.ManagerValue
    if Manager is None:
        raise ValueError("SOLIDWORKS shell lacks its linked configuration manager")
    Config = RequireNative(
        Manager.RootValue.FieldsValue.get("f360"), "moPartConfiguration_c"
    )
    (AtomRow,) = NativeRows(Config.FieldsValue.get("f450"))
    Linked = RequireNative(AtomRow.get("o"), "moLinkedAtomIdNode_c")
    AtomId = AtomNode.FieldsValue["f140"]
    if (
        Config.FieldsValue.get("n450") != 1
        or AtomRow.get("key") != AtomId
        or Linked.FieldsValue.get("f08") != AtomId
        or NativeRecord(Linked.FieldsValue.get("f90"))
        != {"n": 1, "items": [{"v": NativeNodeId(StockNode)}]}
        or NativeRecord(Linked.FieldsValue.get("fd0"))
        != {"n": 1, "items": [{"v": NativeNodeId(ShellNode)}]}
        or not any(
            Entry.EntryValue is Linked and Entry.IndexValue == Linked.IndexValue
            for Entry in Manager.MapValue.EntriesValue
        )
    ):
        raise ValueError("SOLIDWORKS shell linked manager row identifies another body")
