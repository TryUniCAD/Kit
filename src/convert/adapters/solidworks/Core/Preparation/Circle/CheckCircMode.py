from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)


# the independently qualified blind profiles bind each driver type to its actual support and direction
def CheckCircMode(PlanValue: CirclePlan) -> None:
    ScopeValue = (
        PlanValue.AxisValue,
        PlanValue.PlaneName,
        PlanValue.IsDiameter,
        PlanValue.IsReversed,
    )
    if ScopeValue not in (
        ("z", "Front Plane", True, False),
        ("y", "Top Plane", False, True),
    ):
        raise ValueError("circle preparation is outside the qualified blind profiles")
