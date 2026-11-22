from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfPartRead,
)


# each independent setback has its own signed carrier even when both use the same stock edge
def ChmfViewAxes(
    PartValue: ChmfPartRead, *, Secondary: bool = False
) -> tuple[KDatumVector, KDatumVector, KDatumVector]:
    EdgeValue = PartValue.EdgeValue
    Primary = EdgeValue.DistanceAxis
    Other = 3 - Primary - EdgeValue.EdgeAxis
    if Secondary:
        Primary, Other = Other, Primary
    CornerBits = EdgeValue.CornerBits
    SignedU = float(2 * CornerBits[Primary] - 1)
    SignedV = float(2 * CornerBits[Other] - 1)
    AxisU = (
        SignedU if Primary == 0 else 0.0,
        SignedU if Primary == 1 else 0.0,
        SignedU if Primary == 2 else 0.0,
    )
    AxisV = (
        SignedV if Other == 0 else 0.0,
        SignedV if Other == 1 else 0.0,
        SignedV if Other == 2 else 0.0,
    )
    return AxisU, AxisV, CrossVector(AxisU, AxisV)
