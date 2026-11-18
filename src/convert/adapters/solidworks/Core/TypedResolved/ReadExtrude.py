from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Ends.ReadEndMode import ReadEndMode
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureExtrude import ExtrudeEnd


# ordinary boss semantics require actual typed parents and live directions from the retained end specification
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
        raise ValueError("ordinary boss requires one retained profile")
    EndValue = RequireNative(NodeValue.FieldsValue.get("f818"), "moEndSpec_c")
    FieldsValue = EndValue.FieldsValue
    ModeValue = ReadEndMode(FieldsValue)
    FromValue = RequireNative(FieldsValue.get("f140"), "moFromEndSpec_c")
    if (
        type(FromValue.FieldsValue.get("t")) is not int
        or FromValue.FieldsValue["t"] != 0
    ):
        raise ValueError("offset extrusion starts are outside typed blind semantics")
    DepthValue = ReadDepthOwner(LinkValue, RequireNative(FieldsValue.get("f18")))
    SecondValue = None
    if ModeValue == ExtrudeEnd.KTwoLengths:
        SecondValue = ReadDepthOwner(
            LinkValue, RequireNative(FieldsValue.get("f20")), "f20"
        )
        if (
            DepthValue.Parameter is SecondValue.Parameter
            or DepthValue.DepthValue.name == SecondValue.DepthValue.name
            or DepthValue.Dimension.FieldsValue["f50"]
            == SecondValue.Dimension.FieldsValue["f50"]
        ):
            raise ValueError(
                "two direction extrusion requires distinct active driving owners"
            )
    return ExtrudeOwner(
        NodeValue,
        ProfilesValue[0],
        ParentsValue,
        EndValue,
        DepthValue,
        bool(FieldsValue["f8c"]),
        ModeValue,
        SecondValue,
    )
