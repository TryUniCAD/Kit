from interchange.geometry.Models.Sketch import SketchRelation

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxisRule import (
    LineAxisRule,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineValueRule import (
    LineValueRule,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop


# qualified line geometry exposes exactly its owned unary and dimensional relations without inferred coincidence records
def LineRules(
    ProfileId: int, LoopValue: LineLoop, EntityIds: tuple[str, ...]
) -> tuple[SketchRelation, ...]:
    DimsValue = LoopValue.DimsValue
    if DimsValue is None:
        return ()
    return (
        *(
            LineAxisRule(ProfileId, AxisValue, EntityIds)
            for AxisValue in DimsValue.AxisValues
        ),
        *(
            LineValueRule(ProfileId, Driver, LoopValue, EntityIds)
            for Driver in DimsValue.DriverValues
        ),
    )
