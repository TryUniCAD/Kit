from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Core.TypedResolved.Ends.ReadEndMode import ReadEndMode
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureExtrude import ExtrudeEnd


# ordinary extrusion semantics require actual typed parents and live directions from the retained end specification
def ReadExtrude(
    LinkValue: NativeLink,
    NodeValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    IsCut: bool = False,
    *,
    NewSolid: bool = False,
) -> ExtrudeOwner:
    NodeValue = RequireNative(
        NodeValue, "moICE_c" if IsCut or NewSolid else "moExtrusion_c"
    )
    if NewSolid and (IsCut or NodeValue.FieldsValue.get("f810") != 0):
        raise ValueError("independent extrusion requires its actual new solid mode")
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
        raise ValueError("ordinary extrusion requires one retained profile")
    EndValue = RequireNative(NodeValue.FieldsValue.get("f818"), "moEndSpec_c")
    FieldsValue = EndValue.FieldsValue
    ModeValue = ReadEndMode(FieldsValue, AllowThroughAll=IsCut)
    FromValue = RequireNative(FieldsValue.get("f140"), "moFromEndSpec_c")
    if (
        type(FromValue.FieldsValue.get("t")) is not int
        or FromValue.FieldsValue["t"] != 0
    ):
        raise ValueError("offset extrusion starts are outside typed blind semantics")
    if ModeValue == ExtrudeEnd.KThroughAll:
        if (
            NodeValue.ClassValue != RuntimeClass("moICE_c", 1)
            or EndValue.ClassValue != RuntimeClass("moEndSpec_c", 1)
            or FromValue.ClassValue != RuntimeClass("moFromEndSpec_c", 1)
            or FromValue.FieldsValue != {"t": 0}
        ):
            raise ValueError(
                "typed through all cut requires the ordinary start grammar"
            )
        return ExtrudeOwner(
            NodeValue,
            ProfilesValue[0],
            ParentsValue,
            EndValue,
            None,
            bool(FieldsValue["f8c"]),
            ModeValue,
            SecondModeValue=(
                ExtrudeEnd.KThroughAll if FieldsValue["f10"] == 1 else None
            ),
        )
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
        ExtrudeEnd.KBlind if SecondValue is not None else None,
    )
