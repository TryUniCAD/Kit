from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismChain import (
    PrismChain,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFinLinks import (
    PrismFinLinks,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismBody,
)
from interchange.brep.Topology.BrepTopology import BrepEdge


# the body edge chain needs the actual line and its positive fin
def MakePrismEdges(
    EdgesValue: tuple[BrepEdge, ...], FinLinks: PrismFinLinks
) -> tuple[PrismCell, ...]:
    LinksValue = PrismChain(PrismRef(16, EdgeValue.id) for EdgeValue in EdgesValue)
    Values = []
    for EdgeValue in EdgesValue:
        RefValue = PrismRef(16, EdgeValue.id)
        Previous, Following = LinksValue[RefValue]
        Values.append(
            PrismCell(
                RefValue,
                {
                    "owner": KPrismBody,
                    "curve": PrismRef(30, EdgeValue.curve_id),
                    "halfedge": PrismRef(17, FinLinks.EdgeHeads[EdgeValue.id]),
                    "previous": Previous,
                    "next": Following,
                },
            )
        )
    return tuple(Values)
