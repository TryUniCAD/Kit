from math import fsum as SumValues, isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.PlanarMates.EndpointData import (
    EndpointData,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import (
    PlanarMateIn,
)


# ordinary perpendicular construction must reject invalid initial angles rather than claim an unmeasured free degree solver correction
def CheckPerpEnds(
    InputValue: PlanarMateIn, EndValues: tuple[EndpointData, ...]
) -> None:
    if InputValue.KindValue != "perpendicular":
        return
    if len(EndValues) != 2:
        raise ValueError(
            "perpendicular construction requires two actual plane endpoints"
        )
    First, Second = (Value.FrameValue.NormalValue for Value in EndValues)
    if not IsClose(
        SumValues(Value * Other for Value, Other in zip(First, Second, strict=True)),
        0.0,
        rel_tol=0.0,
        abs_tol=1e-10,
    ):
        raise ValueError(
            "perpendicular construction requires orthogonal initial planes"
        )
