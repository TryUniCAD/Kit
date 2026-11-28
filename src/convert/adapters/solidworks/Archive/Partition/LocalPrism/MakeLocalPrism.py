from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismSolid import (
    CheckPrismSolid,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismRings import (
    CheckPrismRings,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismTrims import (
    CheckPrismTrims,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismCarrierCells import (
    MakePrismLines,
    MakePrismPlanes,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismEdges import (
    MakePrismEdges,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismFaces import (
    MakePrismFaces,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismNodes import (
    MakePrismNodes,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismRoot import (
    MakePrismRoot,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeVertexCells import (
    MakeVertexCells,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCarriers import (
    ReadCarriers,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFinLinks import (
    MakeFinLinks,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadPrismFaces import (
    ReadPrismFaces,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.Geometry.Parasolid import BrepTopology
from interchange.brep.Topology.BrepModel import BrepModel


# the local body archive needs resident typed cells computed only from the admitted portable boundary
def MakeLocalPrism(ModelValue: BrepModel) -> tuple[XmtNode, ...]:
    CheckPrismSolid(ModelValue)
    TopologyValue = BrepTopology(ModelValue)
    CarriersValue = ReadCarriers(ModelValue)
    CheckPrismTrims(TopologyValue, CarriersValue)
    FacesValue = ReadPrismFaces(ModelValue, TopologyValue)
    CheckPrismRings(FacesValue, TopologyValue)
    FinLinks = MakeFinLinks(FacesValue, TopologyValue)
    return MakePrismNodes(
        (
            *MakePrismRoot(ModelValue),
            *MakePrismFaces(FacesValue, FinLinks),
            *MakePrismEdges(ModelValue.edges, FinLinks),
            *MakeVertexCells(ModelValue.vertices, FinLinks),
            *MakePrismLines(CarriersValue),
            *MakePrismPlanes(CarriersValue),
        )
    )
