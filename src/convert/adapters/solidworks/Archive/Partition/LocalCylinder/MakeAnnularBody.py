from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckAnnBrep import (
    CheckAnnBrep,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeAnnFaces import (
    MakeAnnFaces,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeAnnGeom import (
    MakeAnnCurves,
    MakeAnnSurfs,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismSolid import (
    CheckPrismSolid,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeBoundRoot import (
    MakeBoundRoot,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismNodes import (
    MakePrismNodes,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismRef
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface
from interchange.brep.Topology.BrepModel import BrepModel


# an annular local solid allocates only the topological and analytic cells it actually transmits
def MakeAnnularBody(ModelValue: BrepModel) -> tuple[XmtNode, ...]:
    CheckPrismSolid(ModelValue)
    CheckAnnBrep(ModelValue, CheckSeams=True)
    TopologyValue = BrepTopology(ModelValue)
    EdgeRefs = tuple(PrismRef(16, Value.id) for Value in ModelValue.edges)
    CurveRefs = tuple(PrismRef(31, Value.curve_id) for Value in ModelValue.edges)
    SurfaceRefs = tuple(
        PrismRef(
            (
                51
                if isinstance(
                    TopologyValue.surface_by_id[Value.surface_id], CylinderSurface
                )
                else 50
            ),
            Value.surface_id,
        )
        for Value in ModelValue.faces
    )
    RootCells = MakeBoundRoot(
        PrismRef(14, ModelValue.faces[0].id), EdgeRefs[0], CurveRefs[0], SurfaceRefs[0]
    )
    return MakePrismNodes(
        (
            *RootCells,
            *MakeAnnFaces(ModelValue, TopologyValue, SurfaceRefs),
            *MakeAnnCurves(ModelValue, TopologyValue, EdgeRefs, CurveRefs),
            *MakeAnnSurfs(ModelValue, TopologyValue, SurfaceRefs),
        )
    )
