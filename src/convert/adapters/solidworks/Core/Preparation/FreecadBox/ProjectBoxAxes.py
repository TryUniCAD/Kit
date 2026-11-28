from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxes import (
    PrincipalAxes,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxisBasis import (
    KAxisBasis,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxis import (
    PrincipalAxis,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxOriginAxes import (
    BoxOriginAxes,
)
from interchange.geometry.Models.Transform import KOriginZero


# source line placement roundoff may identify its verified principal carrier while source ids stay with the intact plan
def ProjectBoxAxes(SourceValue: BoxOriginAxes) -> PrincipalAxes:
    AxesValue: list[PrincipalAxis] = []
    RolesValue = ("X_Axis", "Y_Axis", "Z_Axis")
    for OwnerValue, RoleName, Direction in zip(
        SourceValue.AxisValues, RolesValue, KAxisBasis, strict=True
    ):
        FrameValue = OwnerValue.FrameValue
        SourceAxis = FrameValue.x_axis
        if (
            OwnerValue.RoleName != RoleName
            or FrameValue.origin != KOriginZero
            or not all(
                IsClose(First, Other, rel_tol=0.0, abs_tol=1e-14)
                for First, Other in zip(
                    (SourceAxis.x, SourceAxis.y, SourceAxis.z), Direction, strict=True
                )
            )
        ):
            raise ValueError("FreeCAD origin changed its checked axis carrier or order")
        AxesValue.append(
            PrincipalAxis(
                OwnerValue.LabelValue,
                (0.0, 0.0, 0.0),
                Direction,
                OwnerValue.RecordShown,
            )
        )
    return PrincipalAxes(
        SourceValue.OriginLabel, SourceValue.RecordShown, tuple(AxesValue)
    )
