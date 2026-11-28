from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPocket import (
    CheckPocket,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismSolid import (
    CheckPrismSolid,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismTrims import (
    CheckPrismTrims,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import (
    MakeLocalCells,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.OrientPocket import (
    OrientPocket,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCarriers import (
    ReadCarriers,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadPrismFaces import (
    ReadPrismFaces,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.Geometry.Parasolid import BrepTopology
from interchange.brep.Topology.BrepModel import BrepModel


# a closed pocket uses the same cells as a prism with one additional rim loop
def MakeLocalPocket(ModelValue: BrepModel) -> tuple[XmtNode, ...]:
    CheckPrismSolid(ModelValue, AllowReverse=True)
    Oriented = OrientPocket(ModelValue)
    TopologyValue = BrepTopology(Oriented)
    CarriersValue = ReadCarriers(Oriented)
    CheckPrismTrims(TopologyValue, CarriersValue)
    Boundaries = ReadPrismFaces(Oriented, TopologyValue, AllowPocket=True)
    CheckPocket(Oriented, TopologyValue, Boundaries)
    return MakeLocalCells(Oriented, TopologyValue, CarriersValue, Boundaries)
