from math import fsum as SumValues, isclose as IsClose
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupAxes import (
    CheckGroupAxes,
)


# the first complete multi component group admits already satisfied aligned planes while preserving the signed positive no flip distance branch
def CheckGroupGeom(
    Occurrences: tuple[OccurrenceIn, ...], MateValue: GroupMateIn
) -> None:
    First, Second = (
        Occurrences[Value.OccurrenceIndex].FrameValue for Value in MateValue.EndValues
    )
    NormalValue = CheckGroupAxes(First, Second, MateValue)
    if MateValue.KindValue == "perpendicular":
        return
    Separation = SumValues(
        (Other - Value) * Normal
        for Value, Other, Normal in zip(
            First.OriginValue, Second.OriginValue, NormalValue, strict=True
        )
    )
    if MateValue.KindValue == "coincident" and not IsClose(
        Separation, 0.0, rel_tol=0.0, abs_tol=1e-12
    ):
        raise ValueError("the first planar group requires initially coincident planes")
    if MateValue.DistanceValue is not None and (
        Separation <= 0
        or not IsClose(
            Separation, MateValue.DistanceValue.ValueMetres, rel_tol=0.0, abs_tol=1e-12
        )
    ):
        raise ValueError(
            "planar group distance must match its positive signed authored separation"
        )
