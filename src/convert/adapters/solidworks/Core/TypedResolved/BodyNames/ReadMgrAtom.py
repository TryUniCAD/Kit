from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a single stored kernel body needs one true configuration atom in the inherited graph
def ReadMgrAtom(LinkValue: NativeLink) -> ArchiveNode:
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    Manager = NativeRecord(ModelValue.FieldsValue.get("fd88"))
    ItemsValue = NativeRows(Manager.get("atoms"))
    if len(ItemsValue) != 1 or Manager.get("n6c") != 1:
        raise ValueError("named body has no unique actual atom manager member")
    AtomValue = RequireNative(NativeRecord(ItemsValue[0]).get("o"), "moAtom_c")
    AtomsValue = {
        id(EntryValue.EntryValue)
        for EntryValue in LinkValue.ResolvedValue.MapValue.EntriesValue
        if isinstance(EntryValue.EntryValue, ArchiveNode)
        and EntryValue.EntryValue.ClassValue.NameValue == "moAtom_c"
    }
    if AtomsValue != {id(AtomValue)} or AtomValue.FieldsValue.get("body_kind") != 0:
        raise ValueError("named body has alternate archive atom ownership")
    return AtomValue
