from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the exact live local group must be owned by its feature and the same managed atom
def ReadLocalOwner(
    LinkValue: NativeLink, GroupKey: str, MarkValue: int
) -> tuple[ArchiveNode, int]:
    if any(
        not Report.get("completed")
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
        for Report in (
            LinkValue.ConfigValue.ReportValue,
            LinkValue.ResolvedValue.ReportValue,
        )
    ):
        raise ValueError("local body owners require complete typed archive grammar")
    Features = tuple(
        NodeValue
        for NodeValue in LinkValue.ResolvedValue.RootsValue
        if isinstance(NodeValue, ArchiveNode)
        and NodeValue.ClassValue.NameValue == "moBaseBody_c"
    )
    if len(Features) != 1:
        raise ValueError("local body requires one native BaseBody owner")
    Feature = Features[0]
    FieldsValue = Feature.FieldsValue
    FeatureId = NativeNodeId(Feature)
    if (
        FeatureId <= 0
        or FieldsValue.get("local_body_switch") != 1
        or FieldsValue.get("local_storage_key") != GroupKey
        or ReadNativeName(Feature) != GroupKey
        or FieldsValue.get("segment_mesh_count") != 0
        or RequireNative(FieldsValue.get("f3d0"), "moPMarkRecord_c").FieldsValue.get(
            "f18"
        )
        != MarkValue
    ):
        raise ValueError("native feature does not own the stored local group and mark")
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    Manager = NativeRecord(ModelValue.FieldsValue.get("fd88"))
    RowsValue = NativeRows(Manager.get("atoms"))
    if len(RowsValue) != 1 or Manager.get("n6c") != 1:
        raise ValueError("local body has no unique managed atom")
    AtomValue = RequireNative(RowsValue[0].get("o"), "moAtom_c")
    AtomsValue = {
        id(Entry.EntryValue)
        for Entry in LinkValue.ResolvedValue.MapValue.EntriesValue
        if isinstance(Entry.EntryValue, ArchiveNode)
        and Entry.EntryValue.ClassValue.NameValue == "moAtom_c"
    }
    AtomFields = AtomValue.FieldsValue
    AtomId = AtomFields.get("f140")
    BodyTag = AtomFields.get("f180")
    Identifiers = NativeRows(FieldsValue.get("f498"))
    if (
        AtomsValue != {id(AtomValue)}
        or ReadOutputAtom(Feature) is not AtomValue
        or AtomFields.get("body_kind") != 0
        or AtomFields.get("f12c") != FeatureId
        or AtomFields.get("f130") != FeatureId
        or type(AtomId) is not int
        or AtomId <= 0
        or type(BodyTag) is not int
        or BodyTag < 0
        or AtomFields.get("f1b0") != BodyTag
        or FieldsValue.get("n494") != 1
        or len(Identifiers) != 1
        or Identifiers[0].get("v") != AtomId
    ):
        raise ValueError("local body atom identities disagree")
    return AtomValue, FeatureId
