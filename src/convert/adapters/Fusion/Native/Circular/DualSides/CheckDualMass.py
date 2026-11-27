from convert.adapters.Fusion.Native.Circular.RotaryMass import CacheNumbers
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
)
from convert.Geometry.Extrude.Circular.DualSide.MeasureDualMass import MeasureDualMass
from interchange.Features.DistanceValues import DistExtValues
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import KTransformIdentity, Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# every persisted mass component must agree with independently generated side geometry
def CheckDualMass(
    Context: ExtrudeContext,
    Profile: CircleGeometry,
    Values: DistExtValues,
    Volume: float,
    AreaValue: float,
    Center: SpaceVector,
    FrameValue: Transform = KTransformIdentity,
) -> None:
    if Values.SecondTaperRadians is None:
        raise ValueError("Native circular sides require an independent second taper")
    Diagonal, CrossTerms = MeasureDualMass(
        FrameValue,
        Profile,
        Values.UpperMm,
        -Values.LowerMm,
        Values.TaperRadians,
        Values.SecondTaperRadians,
    )
    Cache = ObjectFields(Context.BodyNode.Fields["cache"])
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
