from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import (
    decode_brep_model as DecodeBrep,
)
from convert.adapters.solidworks.Container.Parasolid import (
    decode_partition_stream as DecodePartition,
)
from convert.adapters.solidworks.Core.Partition.PartTopology import LinearPartBox
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellRings import (
    CheckShellRings,
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
from interchange import TopologySummary
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.Transform import KTransformIdentity


# saved shell qualification needs the actual one planar manifold from the active stream
def CheckShellCache(ModelValue: BrepModel, Footprint: ShellFootprint) -> None:
    (BodyValue,) = ModelValue.bodies
    (RegionValue,) = ModelValue.regions
    if (
        BodyValue.region_ids != (RegionValue.id,)
        or BodyValue.transform != KTransformIdentity
        or BodyValue.wire_ids
        or BodyValue.vertex_ids
        or BodyValue.design_body_id
        or (len(ModelValue.faces), len(ModelValue.edges), len(ModelValue.vertices))
        != (11, 24, 16)
        or LinearPartBox(ModelValue) != Footprint.Bounds
    ):
        raise ValueError(
            "SOLIDWORKS shell active geometry is outside its proven planar body"
        )
    CheckShellRings(ModelValue, Footprint)


# the active saved partition must join the true shell atom before exposing geometry
def ReadShellCache(
    Archive: SldprtArchive,
    AtomValue: ArchiveNode,
    FeatureId: int,
    SelectedMark: int,
    Footprint: ShellFootprint,
) -> ShellCache:
    Footprint.CheckInset()
    StreamName = "Contents/Config-0-Partition"
    Records = DecodePartition(Archive.require(StreamName), StreamName)
    if tuple(Value.kind for Value in Records) != ("partition", "deltas"):
        raise ValueError("SOLIDWORKS shell does not have one active saved partition")
    DataValue = Records[0].data
    NameValue = ReadShellBody(
        ReadActiveNodes(DataValue), AtomValue, FeatureId, SelectedMark
    )
    ModelValue = DecodeBrep(DataValue)
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
    return ShellCache(NameValue, ModelValue, Summary, Centre, Records[0].sha256)
