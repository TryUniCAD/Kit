from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.History.XmtStage import XmtStage
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ReadShellBody import (
    ReadShellBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.History.CheckShellStgs import (
    CheckShellStgs,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.History.CheckStockFaces import (
    CheckStockFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ShellStock import (
    ShellStock,
)


# the removal selection must resolve in the restored stock rather than on the live rim
def CheckShellUndo(
    StagesValue: tuple[XmtStage, ...],
    AtomValue: ArchiveNode,
    StockValue: ShellStock,
    HeaderValue: ArchiveNode,
    Footprint: ShellFootprint,
) -> None:
    Effect = CheckShellStgs(StagesValue)
    Current, Prior = StagesValue[:2]
    StockId = NativeNodeId(StockValue.OwnerValue.NodeValue)
    _ = ReadShellBody(Prior.NodesValue, AtomValue, StockId, 0)
    CapValue = CheckStockFaces(
        Prior.NodesValue, StockValue, DatumTime(HeaderValue, StockId), Footprint
    )
    if CapValue.IndexValue in Current.NodesValue or not any(
        Value is CapValue for Value in Effect.RestoredValue
    ):
        raise ValueError("SOLIDWORKS shell selected cap is not a restored stock owner")
