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
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    PrismMeters,
)
from interchange.brep.Topology.BrepTopology import BrepVertex


# the body vertex and point chains retain reciprocal owners and their actual fin heads
def MakeVertexCells(
    VerticesValue: tuple[BrepVertex, ...], FinLinks: PrismFinLinks
) -> tuple[PrismCell, ...]:
    VertexChain = PrismChain(
        PrismRef(18, VertexValue.id) for VertexValue in VerticesValue
    )
    PointChain = PrismChain(
        PrismRef(29, VertexValue.id) for VertexValue in VerticesValue
    )
    Values: list[PrismCell] = []
    for VertexValue in VerticesValue:
        VertexRef, PointRef = PrismRef(18, VertexValue.id), PrismRef(29, VertexValue.id)
        PreviousVertex, FollowingVertex = VertexChain[VertexRef]
        PreviousPoint, FollowingPoint = PointChain[PointRef]
        Values.extend(
            (
                PrismCell(
                    VertexRef,
                    {
                        "point": PointRef,
                        "owner": KPrismBody,
                        "halfedge": PrismRef(17, FinLinks.VertexHeads[VertexValue.id]),
                        "previous": PreviousVertex,
                        "next": FollowingVertex,
                    },
                ),
                PrismCell(
                    PointRef,
                    {
                        "pvec": PrismMeters(VertexValue.point),
                        "owner": VertexRef,
                        "previous": PreviousPoint,
                        "next": FollowingPoint,
                    },
                ),
            )
        )
    return tuple(Values)
