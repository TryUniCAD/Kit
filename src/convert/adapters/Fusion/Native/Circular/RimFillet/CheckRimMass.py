from convert.adapters.Fusion.Native.Circular.RimFillet.CenterRimTensor import (
    CenterRimTensor,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Circular.RotaryMass import CacheNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
)
from convert.Geometry.Fillet.Circular.RimMoments import RimMoments


# exact solid moments must agree with the complete cached origin and centroidal tensors without wider tolerances
def CheckRimMass(
    Context: RimContext, RadiusMm: float, HeightMm: float, FilletMm: float
) -> None:
    Volume, AreaValue, Center, Radial, Axial = RimMoments(RadiusMm, HeightMm, FilletMm)
    Cache = ObjectFields(Context.Extrusion.BodyNode.Fields["cache"])
    ActualVolume = NumberValue(Cache["volume"])
    ActualCenter = PointCoords(Cache["cog"])
    ActualDiagonal = PointCoords(Cache["moi"])
    ExpectedCenter = (0.0, 0.0, Center / 10)
    ExpectedDiagonal = (
        (Radial + Axial) / 100000,
        (Radial + Axial) / 100000,
        2 * Radial / 100000,
    )
    CacheNumbers(
        (ActualVolume, NumberValue(Cache["area"])), (Volume / 1000, AreaValue / 100)
    )
    CacheNumbers(ActualCenter, ExpectedCenter)
    CacheNumbers(ActualDiagonal, ExpectedDiagonal)
    Actual = CenterRimTensor(
        ActualVolume, ActualCenter, ActualDiagonal, PointCoords(Cache["moiOffDiag"])
    )
    Expected = CenterRimTensor(
        Volume / 1000, ExpectedCenter, ExpectedDiagonal, (0.0, 0.0, 0.0)
    )
    CacheNumbers(Actual[0], Expected[0])
    CacheNumbers(Actual[1], Expected[1])
