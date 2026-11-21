from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# only the real sole manager member may extend the otherwise body free prism inventory
def FindColdAtom(LinkValue: NativeLink) -> ArchiveNode | None:
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    ManagerValue = NativeRecord(ModelValue.FieldsValue.get("fd88"))
    RowsValue = NativeRows(ManagerValue.get("atoms"))
    if not RowsValue and ManagerValue.get("n6c") == 0:
        return None
    if (
        len(RowsValue) != 1
        or ManagerValue.get("n6c") != 1
        or ManagerValue.get("fa8") != 0
    ):
        raise ValueError("cold name requires one fresh actual atom manager member")
    AtomValue = RequireNative(RowsValue[0].get("o"), "moAtom_c")
    Identity = AtomValue.FieldsValue.get("f140")
    if (
        type(Identity) is not int
        or not 0 < Identity < (1 << 31)
        or ManagerValue.get("f260") != Identity
    ):
        raise ValueError("cold atom identity does not match its actual manager counter")
    Atoms = {
        id(Entry.EntryValue)
        for Entry in LinkValue.ResolvedValue.MapValue.EntriesValue
        if isinstance(Entry.EntryValue, ArchiveNode)
        and Entry.EntryValue.ClassValue.NameValue == "moAtom_c"
    }
    if Atoms != {id(AtomValue)}:
        raise ValueError("cold name has extra or detached archive atoms")
    return AtomValue
