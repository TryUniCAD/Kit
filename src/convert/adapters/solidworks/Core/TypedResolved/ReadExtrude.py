from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# blind boss semantics require actual typed parents and the ordinary forward end branch
def ReadExtrude(
    LinkValue: NativeLink, NodeValue: ArchiveNode, Features: Mapping[int, ArchiveNode]
) -> ExtrudeOwner:
    NodeValue = RequireNative(NodeValue, "moExtrusion_c")
    ParentsValue = ReadParents(NodeValue)
    if any(
        Features.get(NativeNodeId(ParentValue)) is not ParentValue
        for ParentValue in ParentsValue
    ):
        raise ValueError("extrusion parent does not alias its resolved feature root")
    ProfilesValue = tuple(
        ParentValue
        for ParentValue in ParentsValue
        if ParentValue.ClassValue.NameValue == "moProfileFeature_c"
    )
    if len(ProfilesValue) != 1:
        raise ValueError("ordinary blind boss requires one retained profile")
    EndValue = RequireNative(NodeValue.FieldsValue.get("f818"), "moEndSpec_c")
    FieldsValue = EndValue.FieldsValue
    for FieldName, Expected in (("f08", 1), ("f0c", 0), ("f10", 0), ("f88", 0)):
        if (
            type(FieldsValue.get(FieldName)) is not int
            or FieldsValue[FieldName] != Expected
        ):
            raise ValueError("extrusion end mode is outside ordinary blind semantics")
    ReverseValue = FieldsValue.get("f8c")
    if type(ReverseValue) is not int or ReverseValue != 0:
        raise ValueError("reversed extrusion is outside typed forward blind semantics")
    FromValue = RequireNative(FieldsValue.get("f140"), "moFromEndSpec_c")
    if (
        type(FromValue.FieldsValue.get("t")) is not int
        or FromValue.FieldsValue["t"] != 0
    ):
        raise ValueError("offset extrusion starts are outside typed blind semantics")
    DepthValue = ReadDepthOwner(LinkValue, RequireNative(FieldsValue.get("f18")))
    return ExtrudeOwner(
        NodeValue,
        ProfilesValue[0],
        ParentsValue,
        EndValue,
        DepthValue,
        bool(ReverseValue),
    )
