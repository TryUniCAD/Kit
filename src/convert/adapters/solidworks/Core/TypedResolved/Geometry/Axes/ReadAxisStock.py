from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.AxisStock import (
    AxisStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.CheckBoxEnd import (
    CheckBoxEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadBoxLoop import (
    ReadBoxLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import (
    CheckBossState,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.VectorSpace import SpaceVector


# only the actual signed top support and one named creator can define this analytic stock
def ReadAxisStock(
    LinkValue: NativeLink, Features: Mapping[int, ArchiveNode], BossValue: ArchiveNode
) -> AxisStock:
    OwnerValue = ReadExtrude(LinkValue, BossValue, Features, AllowReverse=True)
    CheckPrismAtom(BossValue, True)
    CheckBossState(BossValue)
    CheckBoxEnd(OwnerValue)
    ProfileValue = OwnerValue.ProfileValue
    FrameValue = ReadPrismFrame(
        ProfileValue, LinkValue.ConfigValue.RootValue, Features, FrontOnly=False
    )
    Reference = RequireNative(
        ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if type(PlaneId) is not int or FrameValue.z_axis != SpaceVector(0.0, 1.0, 0.0):
        raise ValueError("cache free origin axes require the actual signed top stock")
    return AxisStock(
        OwnerValue, ReadBoxLoop(ProfileValue, LinkValue), FrameValue, PlaneId
    )
