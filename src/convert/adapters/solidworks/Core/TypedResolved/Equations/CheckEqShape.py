from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismRings import (
    RotatePrismRing,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismTrims import (
    CheckPrismTrims,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCarriers import (
    ReadCarriers,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    PrismVector,
)
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqPlanes import (
    CheckEqPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import (
    MakePrismLines,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.Transform import KTransformIdentity


# the cached boundary must agree with the actual solved front sketch and live forward depth
def CheckEqShape(Actual: BrepModel, Model: NativeModel) -> float:
    (SketchValue,) = Model.sketches
    (BossValue,) = Model.operations
    LoopValue, Length = SketchValue.TypedLines, BossValue.length_mm
    if (
        LoopValue is None
        or Length is None
        or Actual.bodies[0].transform != KTransformIdentity
        or any(EdgeValue.degenerate for EdgeValue in Actual.edges)
    ):
        raise ValueError("saved width-depth solid has unsupported placement or trim")
    Expected, _, AreaValue, _ = BuildPrism(
        Actual.bodies[0].design_body_id,
        KTransformIdentity,
        MakePrismLines(LoopValue),
        0.0,
        Length,
    )
    ActualRings = ReadMassRings(Actual)
    ExpectedRings = ReadMassRings(Expected)
    if sorted(
        RotatePrismRing(tuple(map(PrismVector, RingValue))) for RingValue in ActualRings
    ) != sorted(
        RotatePrismRing(tuple(map(PrismVector, RingValue)))
        for RingValue in ExpectedRings
    ):
        raise ValueError("saved width-depth boundary differs from its live dimensions")
    Carriers = ReadCarriers(Actual)
    CheckPrismTrims(BrepTopology(Actual), Carriers)
    CheckEqPlanes(
        Actual, {Plane.id: Plane for Plane in Carriers.PlanesValue}, ActualRings
    )
    return AreaValue
