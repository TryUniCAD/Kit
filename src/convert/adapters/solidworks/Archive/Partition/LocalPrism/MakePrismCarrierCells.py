from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCarriers import (
    PrismCarriers,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismChain import (
    PrismChain,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    PrismMeters,
    PrismVector,
)


# line positions and direction must stay associated with the actual edge
def MakePrismLines(CarriersValue: PrismCarriers) -> tuple[PrismCell, ...]:
    LinksValue = PrismChain(
        PrismRef(30, LineValue.id) for LineValue in CarriersValue.LinesValue
    )
    Values = []
    for LineValue in CarriersValue.LinesValue:
        RefValue = PrismRef(30, LineValue.id)
        Previous, Following = LinksValue[RefValue]
        Values.append(
            PrismCell(
                RefValue,
                {
                    "pvec": PrismMeters(LineValue.origin),
                    "direction": PrismVector(LineValue.direction),
                    "owner": PrismRef(16, CarriersValue.LineOwners[LineValue.id].id),
                    "previous": Previous,
                    "next": Following,
                    "sense": "+",
                },
            )
        )
    return tuple(Values)


# plane carriers preserve the admitted oriented neutral frame and owner
def MakePrismPlanes(CarriersValue: PrismCarriers) -> tuple[PrismCell, ...]:
    LinksValue = PrismChain(
        PrismRef(50, PlaneValue.id) for PlaneValue in CarriersValue.PlanesValue
    )
    Values = []
    for PlaneValue in CarriersValue.PlanesValue:
        RefValue = PrismRef(50, PlaneValue.id)
        Previous, Following = LinksValue[RefValue]
        Values.append(
            PrismCell(
                RefValue,
                {
                    "pvec": PrismMeters(PlaneValue.origin),
                    "normal": PrismVector(PlaneValue.normal),
                    "x_axis": PrismVector(PlaneValue.reference_direction),
                    "owner": PrismRef(14, CarriersValue.PlaneOwners[PlaneValue.id].id),
                    "previous": Previous,
                    "next": Following,
                    "sense": "+",
                },
            )
        )
    return tuple(Values)
