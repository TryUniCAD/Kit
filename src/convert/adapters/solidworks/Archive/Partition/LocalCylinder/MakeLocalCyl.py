from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeCylFaces import (
    MakeCylFaces,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeCylRim import (
    MakeCylRim,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeCylSide import (
    MakeCylSide,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.ReadCylShape import (
    ReadCylShape,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeBoundRoot import (
    MakeBoundRoot,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismNodes import (
    MakePrismNodes,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismRef
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismChain import (
    PrismChain,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.brep.Topology.BrepModel import BrepModel


# the periodic body needs canonical wire allocation from actual source owners alone
def MakeLocalCyl(ModelValue: BrepModel) -> tuple[XmtNode, ...]:
    ShapeValue = ReadCylShape(ModelValue)
    FarRim, NearRim = ShapeValue.FarRim, ShapeValue.NearRim
    FarFace = PrismRef(14, FarRim.CapFace.id)
    EdgeRefs = (PrismRef(16, FarRim.EdgeValue.id), PrismRef(16, NearRim.EdgeValue.id))
    CurveRefs = (
        PrismRef(31, FarRim.CircleValue.id),
        PrismRef(31, NearRim.CircleValue.id),
    )
    SurfaceRefs = (
        PrismRef(51, ShapeValue.MantleValue.id),
        PrismRef(50, FarRim.PlaneValue.id),
        PrismRef(50, NearRim.PlaneValue.id),
    )
    LinksValue = PrismChain(EdgeRefs) | PrismChain(CurveRefs) | PrismChain(SurfaceRefs)
    return MakePrismNodes(
        (
            *MakeBoundRoot(FarFace, EdgeRefs[0], CurveRefs[0], SurfaceRefs[0]),
            *MakeCylFaces(ShapeValue, SurfaceRefs),
            *MakeCylSide(ShapeValue, SurfaceRefs[0], SurfaceRefs[1]),
            *MakeCylRim(FarRim, LinksValue),
            *MakeCylRim(NearRim, LinksValue),
        )
    )
