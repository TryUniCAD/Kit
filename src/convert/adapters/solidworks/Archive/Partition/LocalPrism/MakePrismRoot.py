from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeBoundRoot import (
    MakeBoundRoot,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from interchange.brep.Topology.BrepModel import BrepModel


# finite prism ownership has actual starting vertex and point carriers
def MakePrismRoot(ModelValue: BrepModel) -> tuple[PrismCell, ...]:
    return MakeBoundRoot(
        PrismRef(14, ModelValue.faces[0].id),
        PrismRef(16, ModelValue.edges[0].id),
        PrismRef(30, ModelValue.curves[0].id),
        PrismRef(50, ModelValue.surfaces[0].id),
        PrismRef(18, ModelValue.vertices[0].id),
        PrismRef(29, ModelValue.vertices[0].id),
    )
