from math import isclose as IsClose, pi as PiValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Core.Writing.Circle.ReadCircState import CircState


# native statistics must agree with the actual signed cylinder before and after editing
def CheckCircMass(State: CircState, PlanValue: CirclePlan) -> None:
    Radius = State.RadialValue / (2 if PlanValue.IsDiameter else 1)
    DepthValue = State.DepthValue
    Volume = PiValue * Radius * Radius * DepthValue
    AreaValue = 2 * PiValue * Radius * (Radius + DepthValue)
    FrameValue = PrincipalFrame(PlanValue.AxisValue)
    Offset = DepthValue * (-0.5 if PlanValue.IsReversed else 0.5)
    First, Second = State.CenterValue
    Centroid = tuple(
        First * LocalX + Second * LocalY + Offset * Normal
        for LocalX, LocalY, Normal in zip(
            FrameValue.AxisU, FrameValue.AxisV, FrameValue.NormalValue, strict=True
        )
    )
    if (
        not IsClose(State.VolumeValue, Volume, rel_tol=5e-6)
        or not IsClose(State.AreaValue, AreaValue, rel_tol=5e-6)
        or any(
            not IsClose(Actual, Expected, rel_tol=5e-6, abs_tol=1e-12)
            for Actual, Expected in zip(State.CentroidValue, Centroid, strict=True)
        )
    ):
        raise ValueError("native circle mass differs from its signed cylinder model")
