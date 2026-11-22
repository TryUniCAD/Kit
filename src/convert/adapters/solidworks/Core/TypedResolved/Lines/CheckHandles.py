from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIndex import LineIndex
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint


# adjacency handles must resolve to actual incident lines while retaining distinct tagged object ownership
def CheckHandles(
    PointsValue: tuple[LinePoint, ...], Incident: tuple[set[int], ...]
) -> None:
    Handles = tuple(Handle for Point in PointsValue for Handle in Point.HandlesValue)
    if len({id(Handle) for Handle in Handles}) != 2 * len(PointsValue):
        raise ValueError("typed line ring reuses an endpoint handle object")
    for Point in PointsValue:
        HandleIndices = {
            LineIndex(Handle.FieldsValue, "idx", "f18", 30591)
            for Handle in Point.HandlesValue
        }
        if (
            len(Incident[Point.IndexValue]) != 2
            or HandleIndices != Incident[Point.IndexValue]
            or any(
                Handle.FieldsValue.get("f1c") != -1
                or Handle.FieldsValue.get("f08") != 0
                for Handle in Point.HandlesValue
            )
        ):
            raise ValueError(
                "typed line ring adjacency disagrees with its endpoint handles"
            )
