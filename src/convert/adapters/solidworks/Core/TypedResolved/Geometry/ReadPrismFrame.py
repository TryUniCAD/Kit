from collections.abc import Mapping
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRef import (
    CheckPrismRef,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# source geometry placement must follow the actual datum alias and profile inverse rather than legacy frame scanning
def ReadPrismFrame(
    ProfileValue: ArchiveNode,
    RootValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    *,
    FrontOnly: bool = True,
) -> Transform:
    Reference = RequireNative(
        ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    CheckPrismRef(Reference)
    Fields = Reference.FieldsValue
    Identity = NativeRecord(Fields.get("ff0")).get("f00")
    if type(Identity) is not int or Identity not in Features:
        raise ValueError(
            "cache free prism datum reference is not an actual resolved feature"
        )
    FrameValue, AxisValue = ReadDatumFrame(
        RequireNative(Features[Identity], "moRefPlane_c")
    )
    Component = RequireNative(Fields.get("f58"), "moUnitComponent_c")
    if (
        (FrontOnly and AxisValue != 3)
        or Fields.get("f100") != AxisValue
        or Fields.get("ff8") is not None
    ):
        raise ValueError("cache free prism requires its actual canonical support datum")
    if (
        Component.FieldsValue.get("owner") is not RootValue
        or Component.FieldsValue.get("has_ext") != 0
    ):
        raise ValueError("cache free prism has an external support component")
    if NativeRecord(ProfileValue.FieldsValue.get("pd_ff0")) != FrameXform(FrameValue):
        raise ValueError(
            "cache free prism profile placement differs from its actual datum"
        )
    return Transform(
        SpaceVector(*(Value * 1000 for Value in FrameValue.OriginValue)),
        SpaceVector(*FrameValue.AxisU),
        SpaceVector(*FrameValue.AxisV),
        SpaceVector(*FrameValue.NormalValue),
    )
