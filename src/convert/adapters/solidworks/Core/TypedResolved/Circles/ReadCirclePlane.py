from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.Transform import Transform


# an implicit circular body must use the actual front datum presented in the neutral document
def ReadCirclePlane(
    ModelValue: NativeModel,
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    Profile: ArchiveNode,
) -> tuple[Transform, int]:
    FrameValue = ReadPrismFrame(Profile, LinkValue.ConfigValue.RootValue, Features)
    Reference = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
    PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if type(PlaneId) is not int or not any(
        Plane.object_id == PlaneId for Plane in ModelValue.planes
    ):
        raise ValueError("saved circle has no owned front support datum")
    return FrameValue, PlaneId
