from math import hypot as Hypot
from math import isfinite as IsFinite

from interchange.Features.PlaneExtAxis import GetExtVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# both the definition and its document validator need the same finite directed segment
def GetAxisLine(
    StartValue: SpaceVector, EndValue: SpaceVector
) -> tuple[
    tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
]:
    try:
        StartPoint = GetExtVector(StartValue)
        EndPoint = GetExtVector(EndValue)
    except ValueError as ErrorInfo:
        raise ValueError(
            "plane axis endpoints require finite spatial coordinates"
        ) from ErrorInfo
    DeltaX = float(EndPoint[0]) - float(StartPoint[0])
    DeltaY = float(EndPoint[1]) - float(StartPoint[1])
    DeltaZ = float(EndPoint[2]) - float(StartPoint[2])
    LengthValue = Hypot(DeltaX, DeltaY, DeltaZ)
    if not IsFinite(LengthValue) or LengthValue <= 0.0:
        raise ValueError("plane axis requires distinct endpoints with a finite span")
    return (
        StartPoint,
        EndPoint,
        (
            DeltaX / LengthValue,
            DeltaY / LengthValue,
            DeltaZ / LengthValue,
        ),
    )
