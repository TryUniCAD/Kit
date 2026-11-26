from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.RingMath import (
    IsRingCrossing,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepEdge import (
    SweepEdge,
)


# only adjacent ring edges may touch at their shared authored endpoint
def RejectCrossing(
    FirstValue: SweepEdge | None, SecondValue: SweepEdge | None, CountValue: int
) -> None:
    if (
        FirstValue is None
        or SecondValue is None
        or abs(FirstValue.IndexValue - SecondValue.IndexValue) in (1, CountValue - 1)
    ):
        return
    if IsRingCrossing(
        FirstValue.StartValue,
        FirstValue.EndValue,
        SecondValue.StartValue,
        SecondValue.EndValue,
    ):
        raise ValueError(
            "polygon edges intersect or touch away from their shared endpoints"
        )
