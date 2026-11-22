from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a cold prism must expose the same selected plane and transform used to derive its solid
def ReadPrismSketch(
    Sketch: NativeSketch,
    Profile: ArchiveNode,
    LinkValue: NativeLink,
    NodesValue: Mapping[int, ArchiveNode],
) -> NativeSketch:
    FrameValue = ReadPrismFrame(Profile, LinkValue.ConfigValue.RootValue, NodesValue)
    Reference = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
    PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if type(PlaneId) is not int:
        raise ValueError("sketch does not own its selected support plane")
    return ReplaceValue(Sketch, support_plane_id=PlaneId, TypedFrame=FrameValue)
