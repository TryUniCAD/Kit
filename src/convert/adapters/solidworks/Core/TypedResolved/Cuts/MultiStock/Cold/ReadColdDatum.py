from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.Transform import Transform


# matching support words alone cannot substitute for the live datum and sketch owners
def ReadColdDatum(
    LinkValue: NativeLink,
    ProfileValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
) -> tuple[Transform, ArchiveNode]:
    FrameValue = ReadPrismFrame(
        ProfileValue, LinkValue.ConfigValue.RootValue, Features, FrontOnly=False
    )
    Reference = RequireNative(
        ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    TargetId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if type(TargetId) is not int:
        raise ValueError("cold stock has no actual datum identity")
    DatumValue = RequireNative(Features[TargetId], "moRefPlane_c")
    Component = RequireNative(Reference.FieldsValue.get("f58"), "moUnitComponent_c")
    SketchValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    CheckTreeAlias(LinkValue, (Reference, DatumValue, Component, SketchValue))
    return FrameValue, DatumValue
