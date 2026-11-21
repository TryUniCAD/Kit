from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a wide authored label must come from the actual sole manager member before its full body identity is checked
def ReadBodyAuthor(LinkValue: NativeLink) -> str | None:
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    Manager = NativeRecord(ModelValue.FieldsValue.get("fd88"))
    RowsValue = NativeRows(Manager.get("atoms"))
    if len(RowsValue) != 1 or Manager.get("n6c") != 1:
        raise ValueError("native name has no unique actual archive atom")
    AtomValue = RequireNative(RowsValue[0].get("o"), "moAtom_c")
    FieldsValue = AtomValue.FieldsValue
    if FieldsValue.get("f18") is None and FieldsValue.get("f18c") == 1:
        return None
    if FieldsValue.get("f18") is None or FieldsValue.get("f18c") != 0:
        raise ValueError("native authored body name has an unqualified name state")
    return ReadNativeName(AtomValue)
