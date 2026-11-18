from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedMates.ReadMateIds import ReadMateIds


# separate mate streams must retain registered file identities without colliding with existing model features
def CheckMateIds(NodesValue: tuple[ArchiveNode, ...], LinkValue: NativeLink) -> None:
    Owners = set(IndexFeatures(LinkValue))
    BodyList = RequireRecord(LinkValue.ConfigValue.RootValue.FieldsValue.get("f68"))
    References = ReadRows(RequireRecord(BodyList.get("list")).get("items"))
    ReferenceIds = tuple(
        NativeNodeId(RequireNode(Value.get("o"), "moReference_c"))
        for Value in References
    )
    if len(set(ReferenceIds)) != len(ReferenceIds) or Owners.intersection(ReferenceIds):
        raise ValueError(
            "typed assembly feature identities collide across linked streams"
        )
    Owners.update(ReferenceIds)
    NextValue = FieldInt(LinkValue.ConfigValue.HeaderValue.FieldsValue, "f08")
    for NodeValue in NodesValue:
        Recorded = ReadMateIds(NodeValue)
        if (
            len(set(Recorded)) != len(Recorded)
            or Owners.intersection(Recorded)
            or any(not 0 <= Value < NextValue for Value in Recorded)
        ):
            raise ValueError(
                "typed mate or dimension identity collides or exceeds its header allocation"
            )
        Owners.update(Recorded)
