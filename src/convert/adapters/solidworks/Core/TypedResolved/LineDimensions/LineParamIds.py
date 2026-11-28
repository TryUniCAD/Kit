from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineParamId import (
    LineParamId,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop


# typed sketch dimensions cannot publish dangling references when normal model parameter projection is incomplete
def LineParamIds(
    ProfileId: int, LoopValue: LineLoop, ParameterIds: set[str]
) -> tuple[str, ...]:
    if LoopValue.DimsValue is None:
        return ()
    Values = tuple(
        LineParamId(ProfileId, Driver.NameValue)
        for Driver in LoopValue.DimsValue.DriverValues
    )
    if not set(Values).issubset(ParameterIds):
        raise ValueError("typed rectangle sketch lacks its actual public parameters")
    return Values
