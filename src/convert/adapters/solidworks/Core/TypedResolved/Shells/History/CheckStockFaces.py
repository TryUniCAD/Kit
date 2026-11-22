from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import (
    ReadBodyTree,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellRings import (
    ShellCorner,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.History.ReadShellFace import (
    ReadShellFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.History.ReadStockRing import (
    ReadStockRing,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.History.StockFaceRings import (
    StockFaceRings,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ShellStock import (
    ShellStock,
)


# the previous stock supplies the real removed cap and every adjacent wall owner
def CheckStockFaces(
    NodesValue: Mapping[int, XmtNode],
    StockValue: ShellStock,
    EpochValue: int,
    Footprint: ShellFootprint,
) -> XmtNode:
    StockId = NativeNodeId(StockValue.OwnerValue.NodeValue)
    Expected = StockFaceRings(StockValue, Footprint)
    Actual: dict[tuple[int, int], XmtNode] = {}
    Corners = Footprint.CornerPoints()[:8]
    Tolerance = Footprint.CornerTolerance()
    for IndexValue in ReadBodyTree(NodesValue).FaceIds:
        FaceValue = NodesValue[IndexValue]
        RoleValue = ReadShellFace(NodesValue, FaceValue, StockId, EpochValue)
        if RoleValue is None or RoleValue not in Expected or RoleValue in Actual:
            raise ValueError("SOLIDWORKS shell rollback has a foreign stock face owner")
        Points = ReadStockRing(NodesValue, FaceValue)
        RingValue = frozenset(
            ShellCorner(PointValue, Corners, Tolerance) for PointValue in Points
        )
        if RingValue != Expected[RoleValue]:
            raise ValueError("SOLIDWORKS shell rollback has a different stock trim")
        Actual[RoleValue] = FaceValue
    if Actual.keys() != Expected.keys():
        raise ValueError("SOLIDWORKS shell rollback has incomplete stock face roles")
    return Actual[40, 1]
