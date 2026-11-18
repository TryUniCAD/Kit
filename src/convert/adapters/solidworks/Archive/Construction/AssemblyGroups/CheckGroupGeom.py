from math import fsum as SumValues, isclose as IsClose
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)


# the first complete multi component group admits already satisfied aligned planes while preserving the signed positive no flip distance branch
def CheckGroupGeom(
    Occurrences: tuple[OccurrenceIn, ...], MateValue: GroupMateIn
) -> None:
    First, Second = (
        Occurrences[Value.OccurrenceIndex].FrameValue for Value in MateValue.EndValues
    )
    AxisIndex = "xyz".index(MateValue.EndValues[0].AxisValue)
    NormalValue = (First.AxisU, First.AxisV, First.NormalValue)[AxisIndex]
    OtherNormal = (Second.AxisU, Second.AxisV, Second.NormalValue)[AxisIndex]
    if not IsClose(
        SumValues(
            Value * Other for Value, Other in zip(NormalValue, OtherNormal, strict=True)
        ),
        1.0,
        rel_tol=0.0,
        abs_tol=1e-10,
    ):
        raise ValueError(
            "planar group endpoint normals must have the same measured orientation"
        )
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
