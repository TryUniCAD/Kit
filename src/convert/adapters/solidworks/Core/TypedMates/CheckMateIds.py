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
from convert.adapters.solidworks.Core.TypedMates.CheckMateParam import CheckMateParam


# separate mate streams must retain registered file identities without colliding with existing model features
def CheckMateIds(NodeValue: ArchiveNode, LinkValue: NativeLink) -> None:
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
    MateId = NativeNodeId(NodeValue)
    NextValue = FieldInt(LinkValue.ConfigValue.HeaderValue.FieldsValue, "f08")
    if MateId in Owners or MateId >= NextValue:
        raise ValueError(
            "typed mate persistent identity collides or exceeds its header allocation"
        )
    if NodeValue.ClassValue.NameValue != "moMateDistanceDim_c":
        return
    Display = RequireNode(NodeValue.FieldsValue.get("f4b8"), "moDisplayDistanceDim_c")
    Handles = ReadRows(Display.FieldsValue.get("f850"))
    if len(Handles) != 1:
        raise ValueError("typed distance lacks one allocated dimension")
    Handle = RequireNode(Handles[0].get("o"), "moFeatureDimHandle_c")
    Dimension = RequireNode(Handle.FieldsValue.get("ff0"), "ParallelPlaneDistanceDim_c")
    CheckMateParam(Handle, Dimension)
    DimensionId = FieldInt(Dimension.FieldsValue, "f50")
    if (
        DimensionId < 0
        or DimensionId in Owners
        or DimensionId == MateId
        or DimensionId >= NextValue
    ):
        raise ValueError(
            "typed distance dimension identity collides or exceeds its header allocation"
        )
