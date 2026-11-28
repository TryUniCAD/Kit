from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.LineOrigin import (
    LineOrigin,
)


# embedded external points need their own neutral namespace while retaining the actual sketch creation identity
def OriginPointId(ProfileId: int, OriginValue: LineOrigin) -> str:
    return f"sldprt:sketch:{ProfileId}:external-point:{OriginValue.CreationId}"
