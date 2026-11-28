from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismRef


# the isolated path wire retains both endpoints and opposing edge traversals without a face or loop
@DataClass(frozen=True, slots=True)
class SweepWireRefs:
    ShellValue: PrismRef = PrismRef(13, "path-shell")
    RegionValue: PrismRef = PrismRef(19, "path-region")
    EdgeValue: PrismRef = PrismRef(16, "path-edge")
    ArcValue: PrismRef = PrismRef(31, "path-circle")
    EndValue: PrismRef = PrismRef(18, "path-end")
    StartValue: PrismRef = PrismRef(18, "path-start")
    EndPoint: PrismRef = PrismRef(29, "path-end-point")
    StartPoint: PrismRef = PrismRef(29, "path-start-point")
    FirstFin: PrismRef = PrismRef(17, "path-positive-fin")
    SecondFin: PrismRef = PrismRef(17, "path-negative-fin")
