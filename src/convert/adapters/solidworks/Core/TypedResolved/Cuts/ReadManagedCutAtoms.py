from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the configuration manager and inherited map must agree on every atom in this history
def ReadManagedCutAtoms(LinkValue: NativeLink) -> set[ArchiveNode]:
    RootValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    Manager = NativeRecord(RootValue.FieldsValue.get("fd88"))
    GhostValue = NativeRecord(RootValue.FieldsValue.get("fd90"))
    RowsValue = NativeRows(Manager.get("atoms"))
    ManagedValues = {RequireNative(Row.get("o"), "moAtom_c") for Row in RowsValue}
    MapValues = {
        Entry.EntryValue
        for Entry in LinkValue.ResolvedValue.MapValue.EntriesValue
        if isinstance(Entry.EntryValue, ArchiveNode)
        and Entry.EntryValue.ClassValue.NameValue == "moAtom_c"
    }
    if (
        Manager.get("n6c") != len(RowsValue)
        or len(RowsValue) != len(ManagedValues)
        or ManagedValues != MapValues
        or GhostValue.get("n") != 0
        or GhostValue.get("objects")
    ):
        raise ValueError(
            "cut body atom manager contains missing or additional ownership"
        )
    return ManagedValues
