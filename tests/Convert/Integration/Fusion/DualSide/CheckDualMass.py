from convert.adapters.Fusion.Native.Circular.RotaryMass import CacheNumbers
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
)
from convert.Geometry.Extrude.Circular.DualSide.BuildDualSide import BuildDualSide
from convert.Geometry.Extrude.Circular.DualSide.MeasureDualMass import MeasureDualMass
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase


# native cached tensors independently verify both diagonal and translated cross terms
def CheckDualMass(Sample: DualCase, Context: ExtrudeContext) -> None:
    Diagonal, CrossTerms = MeasureDualMass(
        Sample.Frame,
        Sample.Profile,
        Sample.FirstMm,
        Sample.SecondMm,
        Sample.FirstTaper,
        Sample.SecondTaper,
    )
    Cache = ObjectFields(Context.BodyNode.Fields["cache"])
    Volume, AreaValue, Center = BuildDualSide(
        Sample.Identity,
        Sample.Frame,
        Sample.Profile,
        Sample.FirstMm,
        Sample.SecondMm,
        Sample.FirstTaper,
        Sample.SecondTaper,
    )[1:4]
    CacheNumbers(
        (NumberValue(Cache["volume"]), NumberValue(Cache["area"])),
        (Volume / 1000, AreaValue / 100),
    )
    CacheNumbers(
        PointCoords(Cache["cog"]),
        tuple(Value / 10 for Value in (Center.x, Center.y, Center.z)),
    )
    CacheNumbers(
        PointCoords(Cache["moi"]),
        tuple(Value / 100000 for Value in (Diagonal.x, Diagonal.y, Diagonal.z)),
    )
    CacheNumbers(
        PointCoords(Cache["moiOffDiag"]),
        tuple(Value / 100000 for Value in (CrossTerms.x, CrossTerms.y, CrossTerms.z)),
    )
