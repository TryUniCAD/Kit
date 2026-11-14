from __future__ import annotations

from interchange import CadDocument, LineCurve, PlaneSurface, SpaceVector


def IsAxisLine(Value: SpaceVector) -> bool:
    Components = (Value.x, Value.y, Value.z)
    return sum((abs(ItemData) for ItemData in Components)) == 1.0 and all(
        ItemData in {-1.0, 0.0, 1.0} for ItemData in Components
    )


def HasBoxFaces(
    DocData: CadDocument, LengthValue: float, WidthValue: float, HeightValue: float
) -> bool:
    BrepData = DocData.brep
    if BrepData is None or len(BrepData.curves) != 12 or len(BrepData.surfaces) != 6:
        return False
    if not all(
        (
            isinstance(ItemData, LineCurve) and IsAxisLine(ItemData.direction)
            for ItemData in BrepData.curves
        )
    ):
        return False
    Offsets: dict[int, list[float]] = {0: [], 1: [], 2: []}
    for ItemData in BrepData.surfaces:
        if not isinstance(ItemData, PlaneSurface) or not IsAxisLine(ItemData.normal):
            return False
        Components = (ItemData.normal.x, ItemData.normal.y, ItemData.normal.z)
        AxisValue = next(
            (IndexValue for IndexValue, ValueData in enumerate(Components) if ValueData)
        )
        OriginValue = (ItemData.origin.x, ItemData.origin.y, ItemData.origin.z)
        Offsets[AxisValue].append(abs(Components[AxisValue] * OriginValue[AxisValue]))
    return (
        sorted(Offsets[0]) == sorted((0.0, LengthValue))
        and sorted(Offsets[1]) == sorted((0.0, WidthValue))
        and sorted(Offsets[2]) == sorted((0.0, HeightValue))
    )
