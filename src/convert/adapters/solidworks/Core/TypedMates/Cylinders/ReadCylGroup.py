from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange import MateConstraint, MateGroup, Provenance, ProvenanceSpan


# the loaded mate list belongs to the unique resolved group when no other group state is present
def ReadCylGroup(
    LinkValue: NativeLink, GraphValue: MatesGraph, RuleValue: MateConstraint
) -> MateGroup:
    GroupsValue = {
        NodeValue
        for EntryValue in GraphValue.MapValue.EntriesValue
        if isinstance(NodeValue := EntryValue.EntryValue, ArchiveNode)
        and NodeValue.ClassValue.NameValue == "moMateGroup_c"
    }
    if len(GroupsValue) != 1:
        raise ValueError("concentric mate requires one actual top-level native group")
    (GroupValue,) = GroupsValue
    GroupValue = RequireNative(GroupValue, "moMateGroup_c")
    GroupIndex = GroupValue.IndexValue
    if (
        GroupValue not in LinkValue.ResolvedValue.RootsValue
        or GroupIndex is None
        or GroupIndex < LinkValue.ResolvedValue.MapBase
    ):
        raise ValueError("concentric mate requires one actual top-level native group")
    Fields = GroupValue.FieldsValue
    EmptyList = {"list": {"n": 0, "items": []}, "tail": 0}
    (MateValue,) = GraphValue.RootsValue
    if (
        Fields.get("f60") != EmptyList
        or MateValue.FieldsValue.get("f60") != EmptyList
        or Fields.get("discarded_manager_records#count") != 0
        or Fields.get("discarded_manager_records") != []
        or Fields.get("f4e8#count") != 0
        or Fields.get("f4e8") != []
        or "f4f8" in Fields
        or any(
            Fields.get(NameValue) != 0
            for NameValue in ("f0c", "hidden", "has_list68", "f35c")
        )
    ):
        raise ValueError(
            "concentric mate group has unsupported native state or contents"
        )
    GroupId = NativeNodeId(GroupValue)
    StartValue, EndValue = GroupValue.StartOffset, GroupValue.EndOffset
    if StartValue is None or EndValue is None or not 0 <= StartValue < EndValue:
        raise ValueError("concentric mate group lacks its resolved stream provenance")
    return MateGroup(
        id=f"{RuleValue.owner_definition_id}:mate-group:{GroupId}",
        name=ReadNativeName(GroupValue),
        owner_definition_id=RuleValue.owner_definition_id,
        mate_ids=(RuleValue.id,),
        provenance=Provenance(
            adapter="solidworks.sldasm",
            native_id=str(GroupId),
            spans=(
                ProvenanceSpan(
                    LinkValue.StreamName,
                    StartValue,
                    EndValue - StartValue,
                    "mate-group",
                ),
            ),
        ),
    )
