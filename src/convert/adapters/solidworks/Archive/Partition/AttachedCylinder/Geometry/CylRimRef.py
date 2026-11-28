from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismRef


# each physical station shares one oriented periodic edge between its cap and the side
@DataClass(frozen=True, slots=True)
class CylRimRef:
    FaceValue: PrismRef
    LoopValue: PrismRef
    SideLoop: PrismRef
    EdgeValue: PrismRef
    CurveValue: PrismRef
    PlaneValue: PrismRef
    CapFin: PrismRef
    SideFin: PrismRef
