from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from interchange.Features.FeatureExtrude import ExtrudeEnd


# signed physical stations follow the active native end modes rather than treating a reversed dimension as a negative length
def ReadCircRange(OwnerValue: ExtrudeOwner) -> tuple[float, float]:
    Depth = OwnerValue.RequireDepth().DepthValue.value_mm
    if Depth <= 0.0:
        raise ValueError("cache free circle requires a positive active depth")
    if OwnerValue.ModeValue == ExtrudeEnd.KMidPlane:
        return -Depth * 0.5, Depth * 0.5
    if OwnerValue.ModeValue == ExtrudeEnd.KBlind:
        return (-Depth, 0.0) if OwnerValue.IsReversed else (0.0, Depth)
    if OwnerValue.ModeValue != ExtrudeEnd.KTwoLengths or OwnerValue.SecondValue is None:
        raise ValueError("cache free circle has an unsupported finite end mode")
    Second = OwnerValue.SecondValue.DepthValue.value_mm
    if Second <= 0.0:
        raise ValueError("cache free circle requires a positive second active depth")
    return (-Depth, Second) if OwnerValue.IsReversed else (-Second, Depth)
