from convert.adapters.solidworks.Archive.Construction.Geometry.DotVector import (
    DotVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# the earlier measured mate recipe accumulates each product before adding the next
def SeqDot(
    FirstValue: tuple[float, float, float],
    SecondValue: tuple[float, float, float],
) -> float:
    TotalValue = 0.0
    for LeftValue, RightValue in zip(FirstValue, SecondValue, strict=True):
        TotalValue += LeftValue * RightValue
    return TotalValue


# resolved wrappers store the inverse plane frame with translations derived from the world origin projections
def FrameXform(
    FrameValue: PlaneFrame, *, SequentialProjection: bool = False
) -> dict[str, object]:
    Basis = (FrameValue.AxisU, FrameValue.AxisV, FrameValue.NormalValue)
    Matrix = tuple(Basis[Column][Index] for Index in range(3) for Column in range(3))
    Origin = FrameValue.OriginValue
    Difference = (0.0 - Origin[0], 0.0 - Origin[1], 0.0 - Origin[2])
    ProjectValue = SeqDot if SequentialProjection else DotVector
    Translation = tuple(
        RequireScalar(ProjectValue(Difference, Value)) for Value in Basis
    )
    HasMatrix = int(Matrix != (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
    Result: dict[str, object] = {
        "has_matrix": HasMatrix,
        "f58": Translation[0],
        "f60": Translation[1],
        "f68": Translation[2],
        "f70": 1.0,
        "f78": 0,
    }
    if HasMatrix:
        Result["f08"] = {f"m{Index}": Value for Index, Value in enumerate(Matrix)}
    return Result
