from math import isclose as IsClose

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.DriverLine import (
    DriverLine,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDims import (
    LineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop


# rectangle admission requires complete orthogonal line ownership and independent drivers on both coordinate directions
def CheckDimGraph(LoopValue: LineLoop, DimsValue: LineDims) -> None:
    if len(LoopValue.LinesValue) != 4 or len(LoopValue.PointsValue) != 4:
        raise ValueError("typed rectangle dimensions require exactly four owned lines")
    AxesValue = {
        AxisValue.LineValue: AxisValue.CodeValue for AxisValue in DimsValue.AxisValues
    }
    if set(AxesValue) != {
        LineValue.IndexValue for LineValue in LoopValue.LinesValue
    } or sorted(AxesValue.values()) != [4, 4, 5, 5]:
        raise ValueError("typed rectangle axes do not cover every owned line")
    for LineValue in LoopValue.LinesValue:
        PositionIndex = 1 if AxesValue[LineValue.IndexValue] == 4 else 0
        StartValue = LoopValue.PointsValue[LineValue.StartValue].PositionValue[
            PositionIndex
        ]
        EndValue = LoopValue.PointsValue[LineValue.EndValue].PositionValue[
            PositionIndex
        ]
        if not IsClose(StartValue, EndValue, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("typed rectangle axis disagrees with its selected line")
    Drivers = DimsValue.DriverValues
    OriginValue = DimsValue.OriginValue
    if OriginValue is not None and LoopValue.PointsValue[
        OriginValue.LocalIndex
    ].PositionValue != tuple(Value * 1000.0 for Value in OriginValue.PositionValue):
        raise ValueError(
            "typed origin coincidence does not meet its actual contour corner"
        )
    if not Drivers:
        return
    if (
        len({Driver.NameValue for Driver in Drivers}) != 2
        or len({Driver.NodeValue.FieldsValue["f50"] for Driver in Drivers}) != 2
        or any(
            len({id(getattr(Driver, NameValue)) for Driver in Drivers}) != 2
            for NameValue in ("NodeValue", "ParamValue", "HandleValue", "DisplayValue")
        )
        or {AxesValue[DriverLine(Driver, LoopValue).IndexValue] for Driver in Drivers}
        != {4, 5}
    ):
        raise ValueError(
            "typed rectangle driving graph has shared or incomplete owners"
        )
