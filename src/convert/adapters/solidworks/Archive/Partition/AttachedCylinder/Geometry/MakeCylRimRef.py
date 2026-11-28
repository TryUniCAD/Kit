from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylRimRef import (
    CylRimRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismRef


# near and far keys preserve both uses before their transmit indices exist
def MakeCylRimRef(Station: str) -> CylRimRef:
    return CylRimRef(
        PrismRef(14, Station),
        PrismRef(15, Station + "Cap"),
        PrismRef(15, Station + "Side"),
        PrismRef(16, Station),
        PrismRef(31, Station),
        PrismRef(50, Station),
        PrismRef(17, Station + "Cap"),
        PrismRef(17, Station + "Side"),
    )
