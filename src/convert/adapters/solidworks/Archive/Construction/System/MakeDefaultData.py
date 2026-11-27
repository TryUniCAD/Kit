from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# principal plane geometry derives its inverse frame while empty borders and absent references retain independently documented constructor ownership
def MakeDefaultData(AxisValue: str, FrameValue: PlaneFrame) -> ArchiveNode:
    BasisValue = (FrameValue.AxisU, FrameValue.AxisV, FrameValue.NormalValue)
    TransformValue: dict[str, object] = {
        "has_matrix": int(AxisValue != "z"),
        "f58": 0.0,
        "f60": 0.0,
        "f68": 0.0,
        "f70": 1.0,
        "f78": 0,
    }
    if AxisValue != "z":
        TransformValue["f08"] = {
            f"m{RowValue * 3 + ColumnValue}": BasisValue[ColumnValue][RowValue]
            for RowValue in range(3)
            for ColumnValue in range(3)
        }
    return ArchiveNode(
        RuntimeClass("moDefaultRefPlnData_c", 1),
        {
            "root": dict.fromkeys(("x", "y", "z"), 0.0),
            "normal": dict(zip(("x", "y", "z"), FrameValue.NormalValue, strict=True)),
            "f20": TransformValue,
            "b0": 0.0,
            "b1": 0.0,
            "b2": 0.0,
            "b3": 0.0,
            "f48": None,
            "f50": 0,
            "f54": -4,
            "f58": -4,
            "old_e5": 0,
            "display_root": dict.fromkeys(("x", "y", "z"), 0.0),
            "f5c": 1,
            "f60": 0,
            "f64": 0,
            "f68": None,
            "f70": None,
            "f78": None,
        },
    )
