from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.FeatureKindByNative import KFeatureKindByNative
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Enums.EnumFeatures import FeatureKind


# computed geometry must never qualify a legacy public projection that omitted or misclassified native feature or driver ownership
def CheckPublicGeom(
    ModelValue: NativeModel, Features: Mapping[int, ArchiveNode]
) -> None:
    if (
        ModelValue.TypedGraph.get("status") != "supplemented"
        or not ModelValue.TypedGraph.get("typed_geometry_projection")
        or {Feature.object_id for Feature in ModelValue.features} != set(Features)
    ):
        raise ValueError(
            "cache free prism lacks a complete typed public feature projection"
        )
    if (
        len(ModelValue.operations) != 1
        or len(ModelValue.sketches) != 1
        or ModelValue.sketches[0].TypedLines is None
    ):
        raise ValueError(
            "cache free prism lacks its complete public operation and line intents"
        )
    (BossValue,) = (
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moExtrusion_c"
    )
    (ProfileValue,) = (
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moProfileFeature_c"
    )
    (PublicBoss,) = (
        Feature
        for Feature in ModelValue.features
        if Feature.object_id == NativeNodeId(BossValue)
    )
    Operation = ModelValue.operations[0]
    if (
        Operation.object_id != NativeNodeId(BossValue)
        or Operation.profile_id != NativeNodeId(ProfileValue)
        or Operation.kind != "join"
        or ModelValue.sketches[0].object_id != NativeNodeId(ProfileValue)
        or KFeatureKindByNative.get(PublicBoss.kind.casefold().strip())
        != FeatureKind.KExtrusion
    ):
        raise ValueError(
            "cache free prism public feature semantics differ from native owners"
        )
    Reference = RequireNative(
        ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    if ModelValue.sketches[0].support_plane_id != NativeRecord(
        Reference.FieldsValue.get("ff0")
    ).get("f00"):
        raise ValueError(
            "cache free prism public sketch attachment differs from its native support"
        )
    PlaneIds = {
        Identity
        for Identity, NodeValue in Features.items()
        if NodeValue.ClassValue.NameValue == "moRefPlane_c"
    }
    if (
        len(ModelValue.planes) != len(PlaneIds)
        or {Plane.object_id for Plane in ModelValue.planes} != PlaneIds
    ):
        raise ValueError("cache free prism public plane inventory is incomplete")
    for Plane in ModelValue.planes:
        FrameValue, _ = ReadDatumFrame(Features[Plane.object_id])
        if Plane.origin_mm != tuple(
            Value * 1000 for Value in FrameValue.OriginValue
        ) or (Plane.u_axis, Plane.v_axis, Plane.normal) != (
            FrameValue.AxisU,
            FrameValue.AxisV,
            FrameValue.NormalValue,
        ):
            raise ValueError(
                "cache free prism public placement differs from the actual typed datum"
            )
