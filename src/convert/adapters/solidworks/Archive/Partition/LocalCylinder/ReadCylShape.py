from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckCylSource import (
    CheckCylSource,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.LocalCylShape import (
    LocalCylShape,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.ReadCylRim import (
    ReadCylRim,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismSolid import (
    CheckPrismSolid,
)
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface
from interchange.brep.Topology.BrepModel import BrepModel


# the source boundary owns the mantle and both caps without a synthetic neutral feature
def ReadCylShape(ModelValue: BrepModel) -> LocalCylShape:
    CheckPrismSolid(ModelValue)
    if (
        len(ModelValue.faces) != 3
        or len(ModelValue.face_uses) != 3
        or len(ModelValue.surfaces) != 3
        or len(ModelValue.loops) != 4
        or len(ModelValue.coedges) != 4
        or len(ModelValue.edges) != 2
        or len(ModelValue.curves) != 2
        or len(ModelValue.vertices) != 2
        or any(not FaceValue.same_sense for FaceValue in ModelValue.faces)
    ):
        raise ValueError("local cylinder requires its solid mantle and two caps")
    TopologyValue = BrepTopology(ModelValue)
    Mantles = tuple(
        (FaceValue, Surface)
        for FaceValue in ModelValue.faces
        if type(Surface := TopologyValue.surface_by_id[FaceValue.surface_id])
        is CylinderSurface
    )
    if len(Mantles) != 1 or len(Mantles[0][0].loop_ids) != 2:
        raise ValueError(
            "local cylinder requires two loops on its sole analytic mantle"
        )
    SideFace, MantleValue = Mantles[0]
    FarLoop, NearLoop = (TopologyValue.loops[LoopId] for LoopId in SideFace.loop_ids)
    if not FarLoop.outer or NearLoop.outer:
        raise ValueError("local cylinder mantle has noncanonical loop roles")
    ShapeValue = LocalCylShape(
        SideFace,
        MantleValue,
        ReadCylRim(TopologyValue, FarLoop),
        ReadCylRim(TopologyValue, NearLoop),
    )
    CheckCylSource(ShapeValue, TopologyValue)
    return ShapeValue
