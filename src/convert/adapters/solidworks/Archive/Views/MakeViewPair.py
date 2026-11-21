from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


# native orientation and pan zoom have separate owners despite one semantic camera input
def MakeViewPair(ViewValue: ViewInput) -> tuple[dict[str, object], dict[str, object]]:
    if type(ViewValue) is not ViewInput:
        raise TypeError("native view fields require a validated view input")
    MatrixValues = ViewValue.MatrixValues
    HasMatrix = any(
        Value != float(Index % 4 == 0) for Index, Value in enumerate(MatrixValues)
    )
    ModelRecord: dict[str, object] = {
        "has_matrix": int(HasMatrix),
        "f58": 0.0,
        "f60": 0.0,
        "f68": 0.0,
        "f70": 1.0,
        "f78": 0,
    }
    if HasMatrix:
        ModelRecord["f08"] = {
            f"m{Index}": RequireScalar(Value)
            for Index, Value in enumerate(MatrixValues)
        }
    PanRecord: dict[str, object] = {
        "has_matrix": 0,
        "f58": RequireScalar(ViewValue.ShiftValues[0]),
        "f60": RequireScalar(ViewValue.ShiftValues[1]),
        "f68": RequireScalar(ViewValue.ShiftValues[2]),
        "f70": RequireScalar(ViewValue.ScaleValue),
        "f78": 0,
    }
    return ModelRecord, PanRecord
