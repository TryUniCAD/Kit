from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a saved circular boss must alias the unique live configuration atom it actually produces
def SavedCircleAtom(LinkValue: NativeLink, BossValue: ArchiveNode) -> int:
    Fields = BossValue.FieldsValue
    RowsValue = NativeRows(NativeRecord(Fields.get("f528")).get("items"))
    if (
        Fields.get("has_f528") != 1
        or len(RowsValue) != 1
        or Fields.get("f530") is not None
        or Fields.get("has_f548") != 0
        or Fields.get("f544") != 0
    ):
        raise ValueError("saved circle has more than its single creating body")
    AtomValue = RequireNative(RowsValue[0].get("o"), "moAtom_c")
    AtomFields = AtomValue.FieldsValue
    BodyId = AtomFields.get("f140")
    FeatureId = NativeNodeId(BossValue)
    Atoms = tuple(
        Entry.EntryValue
        for Entry in LinkValue.ConfigValue.MapValue.EntriesValue
        if isinstance(Entry.EntryValue, ArchiveNode)
        and Entry.EntryValue.ClassValue.NameValue == "moAtom_c"
    )
    if (
        len(Atoms) != 1
        or Atoms[0] is not AtomValue
        or type(BodyId) is not int
        or BodyId <= 0
        or AtomFields.get("f130") != FeatureId
        or AtomFields.get("f12c") != FeatureId
        or AtomFields.get("f18c") != 1
        or AtomFields.get("body_kind") != 0
        or NativeRows(Fields.get("f498")) != ({"v": BodyId},)
    ):
        raise ValueError(
            "saved circle atom does not link its producing boss and configuration"
        )
    return BodyId
