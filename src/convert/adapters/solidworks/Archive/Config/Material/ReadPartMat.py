from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Config.Material.CfgMatGraph import CfgMatGraph
from convert.adapters.solidworks.Archive.Config.Material.MakeMatCtx import MakeMatCtx
from convert.adapters.solidworks.Archive.Config.Material.MatTypes import (
    KHatchClass,
    KMaterialClass,
    KModelDataClass,
)
from convert.adapters.solidworks.Archive.Config.Material.ReadMatRoleMut import (
    ReadMatRoleMut,
)
from convert.adapters.solidworks.Archive.Config.Material.ReadMatVizMut import (
    ReadMatVizMut,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader


# the physical suffix must consume its bounded fields and preserve the part map
def ReadPartMat(
    BufferValue: bytes,
    VersionValue: int,
    SeedValue: MapSnapshot,
    ModelValue: ArchiveNode,
    *,
    ConditionBits: int = 0,
) -> CfgMatGraph:
    ContextValue = MakeMatCtx(VersionValue, ConditionBits)
    Cursor = BinaryReader(BufferValue)
    MapValue = ArchiveMaps(SeedValue.CounterValue, SeedValue)
    if ModelValue.ClassValue != KPartRoot or ObjectIndex(MapValue, ModelValue) is None:
        raise BodyUnsupported("SOLIDWORKS part material requires its mapped part owner")
    Fields: dict[str, object] = {
        "f1418": ReadMatRoleMut(Cursor, MapValue, ContextValue, KHatchClass),
        "f1420": ReadMatRoleMut(
            Cursor, MapValue, ContextValue, KMaterialClass, AllowNull=True
        ),
        "f1588": ReadMatRoleMut(Cursor, MapValue, ContextValue, KModelDataClass),
        "f938": ReadMatVizMut(Cursor),
    }
    if Cursor.GetRemaining():
        raise BodyUnsupported("SOLIDWORKS part material suffix has trailing data")
    ContextValue.UsageValue.IsComplete = True
    return CfgMatGraph(
        Fields, MapValue.Snapshot(), GetBodyReport(ContextValue.UsageValue)
    )
