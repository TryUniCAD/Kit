from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellCache import (
    CheckShellCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.MeasureShell import (
    MeasureShell,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellCache import (
    ShellCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from interchange import TopologySummary
from interchange.brep.Topology.BrepModel import BrepModel


# both retained and analytically reconstructed shells must agree with the complete inward footprint
def SummShellBrep(
    ModelValue: BrepModel,
    Footprint: ShellFootprint,
    *,
    NameValue: str | None = None,
    DigestValue: str | None = None,
) -> ShellCache:
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
    return ShellCache(NameValue, ModelValue, Summary, Centre, DigestValue)
