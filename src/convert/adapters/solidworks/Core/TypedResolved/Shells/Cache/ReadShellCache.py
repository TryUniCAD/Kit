from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtStages import (
    ReadXmtStages,
)
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import (
    decode_brep_model as DecodeBrep,
)
from convert.adapters.solidworks.Container.Parasolid import (
    decode_partition_stream as DecodePartition,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellCache import (
    CheckShellCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.MeasureShell import (
    MeasureShell,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ReadShellBody import (
    ReadShellBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellCache import (
    ShellCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.History.CheckShellUndo import (
    CheckShellUndo,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ShellStock import (
    ShellStock,
)
from interchange import TopologySummary


# the active saved partition must join the true shell atom before exposing geometry
def ReadShellCache(
    Archive: SldprtArchive,
    AtomValue: ArchiveNode,
    StockValue: ShellStock,
    FeatureId: int,
    MarksValue: tuple[int, int, int],
    HeaderValue: ArchiveNode,
    Footprint: ShellFootprint,
) -> ShellCache:
    Footprint.CheckInset()
    Records = DecodePartition(Archive.require(KPartitionStream), KPartitionStream)
    if tuple(Value.kind for Value in Records) != ("partition", "deltas"):
        raise ValueError("SOLIDWORKS shell does not have one active saved partition")
    Current, History = Records
    NodesValue = ReadActiveNodes(Current.data)
    NameValue = ReadShellBody(NodesValue, AtomValue, FeatureId, MarksValue[-1])
    StagesValue = ReadXmtStages(History.data, NodesValue, MarksValue)
    CheckShellUndo(StagesValue, AtomValue, StockValue, HeaderValue, Footprint)
    ModelValue = DecodeBrep(Current.data)
    if ModelValue is None:
        raise ValueError("SOLIDWORKS shell active geometry cannot be decoded")
    CheckShellCache(ModelValue, Footprint)
    Volume, SurfaceArea, Centre = MeasureShell(ModelValue, Footprint)
    Summary = TopologySummary(
        solid_count=1,
        shell_count=1,
        face_count=11,
        edge_count=24,
        vertex_count=16,
        volume=Volume,
        surface_area=SurfaceArea,
        bounding_box=Footprint.Bounds,
    )
    return ShellCache(NameValue, ModelValue, Summary, Centre, Current.sha256)
