from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismRef


# the section sheet binds one periodic edge and the two opposite fins to its planar support
@DataClass(frozen=True, slots=True)
class SweepSheetRefs:
    ShellValue: PrismRef = PrismRef(13, "sheet")
    PlaneValue: PrismRef = PrismRef(50, "section-plane")
    ArcValue: PrismRef = PrismRef(31, "section-circle")
    RegionValue: PrismRef = PrismRef(19, "section-region")
    EdgeValue: PrismRef = PrismRef(16, "periodic-edge")
    FaceValue: PrismRef = PrismRef(14, "section-face")
    LoopValue: PrismRef = PrismRef(15, "section-loop")
    FirstFin: PrismRef = PrismRef(17, "loop-use")
    SecondFin: PrismRef = PrismRef(17, "free-side-use")
