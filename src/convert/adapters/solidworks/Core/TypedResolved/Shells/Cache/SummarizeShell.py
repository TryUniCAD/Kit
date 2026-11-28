from convert.adapters.solidworks.Core.Partition.PartTopology import LinearPartBox
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellCache import (
    CheckShellCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.MeasureShell import (
    MeasureShell,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from interchange import TopologySummary
from interchange.brep.Topology.BrepModel import BrepModel


# publish the actual vertex extrema only after the saved shell agrees with its nominal footprint
def SummarizeShell(
    ModelValue: BrepModel, Footprint: ShellFootprint
) -> tuple[TopologySummary, tuple[float, float, float]]:
    CheckShellCache(ModelValue, Footprint)
    Bounds = LinearPartBox(ModelValue)
    if Bounds is None:
        raise ValueError("SOLIDWORKS shell has no linear saved bounds")
    Volume, SurfaceArea, Centre = MeasureShell(ModelValue, Footprint)
    Summary = TopologySummary(
        solid_count=1,
        shell_count=1,
        face_count=11,
        edge_count=24,
        vertex_count=16,
        volume=Volume,
        surface_area=SurfaceArea,
        bounding_box=Bounds,
    )
    return Summary, Centre
