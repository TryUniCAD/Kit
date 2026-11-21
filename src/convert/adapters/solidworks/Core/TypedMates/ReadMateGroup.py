from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedMates.MateProvenance import MateProvenance
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange import MateConstraint, MateGroup, Provenance, ProvenanceSpan


# a separate mate list can supply group membership only for one actual flat resolved owner
def ReadMateGroup(
    LinkValue: NativeLink,
    GraphValue: MatesGraph,
    RulesValue: tuple[MateConstraint, ...],
    RootId: str,
) -> MateGroup:
    GroupsValue = tuple(
        EntryValue
        for EntryValue in GraphValue.MapValue.EntriesValue
        if isinstance(NodeValue := EntryValue.EntryValue, ArchiveNode)
        and NodeValue.ClassValue.NameValue == "moMateGroup_c"
    )
    if len(GroupsValue) != 1:
        raise ValueError("typed mates require one actual top-level native group")
    (GroupEntry,) = GroupsValue
    GroupValue = RequireNative(GroupEntry.EntryValue, "moMateGroup_c")
    Resolved = LinkValue.ResolvedValue
    if (
        Resolved.RootsValue.count(GroupValue) != 1
        or GroupValue.IndexValue != GroupEntry.IndexValue
        or GraphValue.MapBase != Resolved.MapValue.CounterValue
        or not Resolved.MapBase <= GroupEntry.IndexValue < GraphValue.MapBase
        or GroupEntry not in Resolved.MapValue.EntriesValue
        or any(
            GroupValue in ReadChildren(NodeValue)
            for NodeValue in Resolved.RootsValue
            if isinstance(NodeValue, ArchiveNode)
            and NodeValue is not GroupValue
            and "f60" in NodeValue.FieldsValue
        )
    ):
        raise ValueError("typed mates require one actual top-level native group")
    Fields = GroupValue.FieldsValue
    EmptyList = {"list": {"n": 0, "items": []}, "tail": 0}
    UpdateWord = Fields.get("f0c")
    MemberWord = 0x100 if UpdateWord == 0 else 1
    if (
        type(UpdateWord) is not int
        or UpdateWord not in (0, 1)
        or Fields.get("f60") != EmptyList
        or Fields.get("discarded_manager_records#count") != 0
        or Fields.get("discarded_manager_records") != []
        or Fields.get("f4e8#count") != 0
        or Fields.get("f4e8") != []
        or "f4f8" in Fields
        or any(
            Fields.get(NameValue) != 0 for NameValue in ("hidden", "has_list68", "f35c")
        )
        or any(
            NodeValue.FieldsValue.get("f60") != EmptyList
            or NodeValue.FieldsValue.get("f0c") != MemberWord
            for NodeValue in GraphValue.RootsValue
        )
    ):
        raise ValueError("typed mate group has unsupported native state or contents")
    MateIds = tuple(RuleValue.id for RuleValue in RulesValue)
    if (
        not MateIds
        or len(MateIds) != len(GraphValue.RootsValue)
        or len(set(MateIds)) != len(MateIds)
        or any(
            RuleValue.owner_definition_id != RootId
            or RuleValue.order != Ordinal
            or RuleValue.provenance != MateProvenance(NodeValue)
            for Ordinal, (NodeValue, RuleValue) in enumerate(
                zip(GraphValue.RootsValue, RulesValue, strict=True)
            )
        )
    ):
        raise ValueError(
            "typed mate group membership differs from the owned native list"
        )
    GroupId = NativeNodeId(GroupValue)
    StartValue, EndValue = GroupValue.StartOffset, GroupValue.EndOffset
    if StartValue is None or EndValue is None or not 0 <= StartValue < EndValue:
        raise ValueError("typed mate group lacks its resolved stream provenance")
    return MateGroup(
        id=f"{RootId}:mate-group:{GroupId}",
        name=ReadNativeName(GroupValue),
        owner_definition_id=RootId,
        mate_ids=MateIds,
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
