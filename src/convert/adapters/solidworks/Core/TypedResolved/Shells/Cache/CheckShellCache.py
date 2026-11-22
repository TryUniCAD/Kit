from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellRings import (
    CheckShellRings,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
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
    ):
        raise ValueError(
            "SOLIDWORKS shell active geometry is outside its proven planar body"
        )
    CheckShellRings(ModelValue, Footprint)
