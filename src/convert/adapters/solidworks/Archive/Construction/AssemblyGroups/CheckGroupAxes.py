from math import fsum as SumValues, isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)


# endpoint geometry must use each actual selected datum axis while preserving the measured orientation requirement for existing aligned kinds
def CheckGroupAxes(
    First: PlaneFrame, Second: PlaneFrame, MateValue: GroupMateIn
) -> tuple[float, float, float]:
    FirstAxis, SecondAxis = (
        "xyz".index(Value.AxisValue) for Value in MateValue.EndValues
    )
    NormalValue = (First.AxisU, First.AxisV, First.NormalValue)[FirstAxis]
    OtherNormal = (Second.AxisU, Second.AxisV, Second.NormalValue)[SecondAxis]
    IsPerpendicular = MateValue.KindValue == "perpendicular"
    if not IsClose(
        SumValues(
            Value * Other for Value, Other in zip(NormalValue, OtherNormal, strict=True)
        ),
        0.0 if IsPerpendicular else 1.0,
        rel_tol=0.0,
        abs_tol=1e-10,
    ):
        raise ValueError(
            "perpendicular group endpoints must be orthogonal"
            if IsPerpendicular
            else "planar group endpoint normals must have the same measured orientation"
        )
    return NormalValue
