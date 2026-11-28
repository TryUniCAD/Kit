from math import dist as Distance, isclose as IsClose, pi as PiValue

from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.Geometry.EllipMeasures import (
    EllipPerim,
)


# each lifecycle observation must describe the model section swept through the actual reported depth
def CheckEllipMass(
    PlanValue: EllipsePlan, StateValue: tuple[float, ...], DepthValue: float
) -> None:
    CenterValue = PlanValue.CenterValue
    FirstRadius = Distance(CenterValue, PlanValue.MajorValue)
    SecondRadius = Distance(CenterValue, PlanValue.MinorValue)
    CapArea = PiValue * FirstRadius * SecondRadius
    Expected = (
        CapArea * DepthValue,
        2.0 * CapArea + EllipPerim(FirstRadius, SecondRadius) * DepthValue,
        *CenterValue,
        DepthValue / 2,
    )
    if any(
        not IsClose(
            Actual, Target, rel_tol=5e-7, abs_tol=1e-11 if abs(Target) < 1e-11 else 0.0
        )
        for Actual, Target in zip(StateValue[1:], Expected, strict=True)
    ):
        raise ValueError("ellipse measurement disagrees with the generated swept solid")
