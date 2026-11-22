from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxes import (
    PrincipalAxes,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxisBasis import (
    KAxisBasis,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxis import (
    PrincipalAxis,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from typing import cast as CastValue


# unsupported source visibility or carriers must refuse before any principal display changes
def CheckAxisInput(AxesValue: PrincipalAxes, InputValue: PartBuildInput) -> None:
    if type(AxesValue) is not PrincipalAxes or (
        AxesValue.OriginShown is not True
        or AxesValue.OriginName != InputValue.SystemValue.OriginName
        or len(AxesValue.AxisValues) != len(KAxisBasis)
    ):
        raise ValueError("principal axes require the actual enabled model origin")
    for AxisValue, Direction in zip(AxesValue.AxisValues, KAxisBasis, strict=True):
        if (
            type(AxisValue) is not PrincipalAxis
            or not isinstance(CastValue(object, AxisValue.NameValue), str)
            or not AxisValue.NameValue.strip()
            or not AxisValue.NameValue.isprintable()
            or AxisValue.IsVisible is not True
            or AxisValue.OriginValue != (0.0, 0.0, 0.0)
            or AxisValue.DirectionValue != Direction
        ):
            raise ValueError(
                "unsupported principal axis name, carrier, order or visibility"
            )
