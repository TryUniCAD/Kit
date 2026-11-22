from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)


# the cold rotated inspection profile has separate native event and archive evidence from ordinary public assembly generation
def CheckWriteMates(
    PlacesValue: tuple[OccurrenceIn, ...], RulesValue: tuple[GroupMateIn, ...]
) -> None:
    if len(PlacesValue) != 2 or tuple(
        (Value.KindValue, Value.EndValues[0].AxisValue) for Value in RulesValue
    ) != (("parallel", "z"), ("distance", "y"), ("coincident", "x")):
        return
    FirstValue, SecondValue = (Value.FrameValue for Value in PlacesValue)
    Tolerance = 1e-12
    if (
        abs(FirstValue.AxisU[0]) > Tolerance
        and abs(FirstValue.AxisU[1]) > Tolerance
        and all(
            IsClose(Value, Other, rel_tol=0.0, abs_tol=Tolerance)
            for Value, Other in zip(
                (*FirstValue.NormalValue, *SecondValue.NormalValue, *SecondValue.AxisU),
                (0.0, 0.0, 1.0, 0.0, 0.0, 1.0, *FirstValue.AxisU),
                strict=True,
            )
        )
    ):
        raise ValueError(
            "the rotated three-mate profile requires separate native writer qualification"
        )
