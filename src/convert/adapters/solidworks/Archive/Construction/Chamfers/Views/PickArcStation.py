from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumDot,
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAngleArc import (
    KArcTolerance,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)


# the ordinary acute arc checks the first exterior branch before considering the second
def PickArcStation(
    FirstRay: KDatumVector, OtherRay: KDatumVector, Direction: KDatumVector
) -> float:
    Crossing = CrossVector(FirstRay, OtherRay)
    if Crossing[2] > KArcTolerance:
        FirstScore = DatumDot(CrossVector(FirstRay, Direction), Crossing)
        if FirstScore < -KArcTolerance:
            return -0.5
        OtherScore = DatumDot(CrossVector(OtherRay, Direction), Crossing)
        if FirstScore > KArcTolerance and OtherScore > KArcTolerance:
            return 1.5
    raise ValueError("chamfer angle label requires a proven exterior witness placement")
