from math import fsum as SumValues, isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylPlace import (
    CylPlace,
)


# the generated mate assumes an independently authored coaxial pose and must never solve or change it
def CheckCylPose(First: CylPlace, Second: CylPlace, AlignmentCode: int) -> None:
    Alignment = SumValues(
        Value * Other
        for Value, Other in zip(First.WorldAxis, Second.WorldAxis, strict=True)
    )
    DeltaValue = tuple(
        Other - Value
        for Value, Other in zip(First.OriginValue, Second.OriginValue, strict=True)
    )
    SlideValue = SumValues(
        Value * AxisItem
        for Value, AxisItem in zip(DeltaValue, First.WorldAxis, strict=True)
    )
    if not IsClose(
        Alignment, 1.0 if AlignmentCode == 1 else -1.0, rel_tol=1e-10, abs_tol=1e-12
    ) or any(
        not IsClose(Value - SlideValue * AxisItem, 0.0, abs_tol=1e-12)
        for Value, AxisItem in zip(DeltaValue, First.WorldAxis, strict=True)
    ):
        raise ValueError(
            "explicit prepositioned cylinder axes do not satisfy the selected alignment"
        )
