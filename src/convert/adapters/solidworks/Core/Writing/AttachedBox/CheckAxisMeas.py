from math import isclose as IsClose

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxOriginAxes import (
    BoxOriginAxes,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxMeasArray import (
    BoxMeasArray,
)

# native axis dependencies follow the signed normal ordering of the standard principal datums
KBoxAxisParents = (
    ("Top Plane", "Front Plane"),
    ("Front Plane", "Right Plane"),
    ("Right Plane", "Top Plane"),
)


# selected axis directions and finite stops are measured in each independent stock state
def CheckAxisMeas(
    Actual: object, AxesValue: BoxOriginAxes, Lengths: tuple[float, float, float]
) -> None:
    Values = ReadMeasMap(Actual)
    if set(Values) != {Value.LabelValue for Value in AxesValue.AxisValues}:
        raise ValueError("attached box measurement lacks all actual axis owners")
    Length, Width, Height = Lengths
    Limits = ((0.0, Length), (-Height, 0.0), (0.0, Width))
    for AxisIndex, (AxisValue, Parents, (Lower, Upper)) in enumerate(
        zip(AxesValue.AxisValues, KBoxAxisParents, Limits, strict=True)
    ):
        RowValue = ReadMeasMap(Values[AxisValue.LabelValue])
        Extents = BoxMeasArray(RowValue.get("endpoints_m"), 2)
        Margin = (Upper - Lower) * 0.05
        Start, EndValue = Lower - Margin, Upper + Margin
        if (
            RowValue.get("selectable") is not True
            or RowValue.get("parents") != list(Parents)
            or RowValue.get("unit") != [float(Value == AxisIndex) for Value in range(3)]
        ):
            raise ValueError(
                "attached box measurement has contradictory native axis support"
            )
        for PointValue, Station in zip(Extents, (Start, EndValue), strict=True):
            if any(
                not IsClose(
                    RequireScalar(ActualValue),
                    Station if CoordIndex == AxisIndex else 0.0,
                    rel_tol=5e-7,
                    abs_tol=1e-15,
                )
                for CoordIndex, ActualValue in enumerate(BoxMeasArray(PointValue, 3))
            ):
                raise ValueError(
                    "attached box measurement axes do not meet their signed finite stock"
                )
