from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRoots import (
    ReadChmfRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfStock import (
    ReadChmfStock,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import (
    CheckBossState,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Shells.Owners.CheckShellFresh import (
    CheckShellFresh,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.CheckShellEnd import (
    CheckShellEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ReadStockLoop import (
    ReadStockLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ShellStock import (
    ShellStock,
)
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorSpace import SpaceVector


# rectangular saved stock uses its actual front datum and finite forward blind driver
def ReadShellStock(
    LinkValue: NativeLink, StockNode: ArchiveNode, Features: Mapping[int, ArchiveNode]
) -> ShellStock:
    Owner = ReadExtrude(LinkValue, StockNode, Features)
    ProfileValue = Owner.ProfileValue
    CheckBossState(StockNode)
    CheckShellEnd(Owner)
    CheckPrismProf(ProfileValue, IsSaved=True)
    ModelRoot = LinkValue.ConfigValue.RootValue
    if ReadPrismFrame(
        ProfileValue, ModelRoot, Features
    ) != KTransformIdentity or Owner.ParentsValue != (ProfileValue,):
        raise ValueError(
            "SOLIDWORKS shell stock requires the ordinary local Front plane"
        )
    return ShellStockBox(Owner, ReadStockLoop(ProfileValue, LinkValue))


# the fresh stock shares the qualified rectangular profile and finite blind end
def ReadFreshStock(
    LinkValue: NativeLink,
    ModelValue: NativeModel,
    StockNode: ArchiveNode,
    ShellNode: ArchiveNode,
) -> tuple[ShellStock, tuple[ArchiveNode, ...]]:
    CheckShellFresh(LinkValue, ShellNode)
    _, Features = ReadChmfRoots(LinkValue, ModelValue, ShellNode)
    OwnerValue, _, LoopValue = ReadChmfStock(LinkValue, StockNode, Features)
    return ShellStockBox(OwnerValue, LoopValue), tuple(Features.values())


# both stock layouts derive extents and port the actual selected support from the same owners
def ShellStockBox(Owner: ExtrudeOwner, LoopValue: LineLoop) -> ShellStock:
    Positions = {Point.PositionValue for Point in LoopValue.PointsValue.values()}
    XValues = sorted({XValue for XValue, _ in Positions})
    YValues = sorted({YValue for _, YValue in Positions})
    DepthValue = Owner.RequireDepth().DepthValue.value_mm
    if (
        len(Positions) != 4
        or len(XValues) != 2
        or len(YValues) != 2
        or DepthValue is None
        or DepthValue <= 0
    ):
        raise ValueError("SOLIDWORKS shell stock requires a finite forward rectangle")
    Bounds = BoundingBox(
        SpaceVector(XValues[0], YValues[0], 0.0),
        SpaceVector(XValues[1], YValues[1], DepthValue),
    )
    Support = RequireNative(
        Owner.ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    PlaneId = NativeRecord(Support.FieldsValue.get("ff0")).get("f00")
    if type(PlaneId) is not int:
        raise ValueError("SOLIDWORKS shell stock lost its actual datum identity")
    return ShellStock(Owner, LoopValue, Bounds, PlaneId)
