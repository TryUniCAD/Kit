from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckMember import (
    CheckMember,
)


# every removed legacy row must bind to an actual owned member or a proven empty direct configuration helper
def CheckExtras(
    Model: NativeModel,
    RootsValue: tuple[ArchiveNode, ...],
    MembersValue: tuple[ArchiveNode, ...],
    HelpersValue: tuple[Mapping[str, object], ...],
) -> None:
    RootIds = {NativeNodeId(NodeValue) for NodeValue in RootsValue}
    MemberIds = {NativeNodeId(NodeValue) for NodeValue in MembersValue}
    FeatureIds = tuple(Feature.object_id for Feature in Model.features)
    if len(set(FeatureIds)) != len(FeatureIds) or not RootIds.issubset(FeatureIds):
        raise ValueError("ordinary presentation lacks unique public root identities")
    if len(MemberIds) != len(MembersValue) or RootIds.intersection(MemberIds):
        raise ValueError("system member identity collides with a modeling root")
    for Feature in Model.features:
        if Feature.object_id in RootIds:
            continue
        if Feature.dimensions:
            raise ValueError("legacy presentation row owns unmodeled dimensions")
        if set(Feature.properties).difference(("id", "Name", "Type")):
            raise ValueError("legacy presentation row retains unmodeled keyword fields")
        if Feature.object_id in MemberIds:
            Member = next(
                NodeValue
                for NodeValue in MembersValue
                if NativeNodeId(NodeValue) == Feature.object_id
            )
            CheckMember(Feature, Member)
            continue
        if not any(
            Feature.object_id == Helper["stored_node_id"]
            and Feature.kind == Helper["legacy_kind"]
            and Feature.native_offset is None
            and Feature.native_end is None
            and not Feature.properties.get("Name")
            for Helper in HelpersValue
        ):
            raise ValueError("legacy presentation includes an unaccounted feature")
