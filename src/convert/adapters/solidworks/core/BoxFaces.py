from __future__ import annotations

import math as MathValue

from interchange import CadDocument, LineCurve, PlaneSurface, SpaceVector

from convert.adapters.solidworks.core.BrepIdentity import IsIdentity


def IsAxisLine(Value: SpaceVector) -> bool:
    Components = (Value.x, Value.y, Value.z)
    return sum((abs(ItemData) for ItemData in Components)) == 1.0 and all(
        ItemData in {-1.0, 0.0, 1.0} for ItemData in Components
    )


def IsOnLine(Curve: LineCurve, Point: SpaceVector) -> bool:
    Delta = (
        Point.x - Curve.origin.x,
        Point.y - Curve.origin.y,
        Point.z - Curve.origin.z,
    )
    Direction = (Curve.direction.x, Curve.direction.y, Curve.direction.z)
    Cross = (
        Delta[1] * Direction[2] - Delta[2] * Direction[1],
        Delta[2] * Direction[0] - Delta[0] * Direction[2],
        Delta[0] * Direction[1] - Delta[1] * Direction[0],
    )
    return all(abs(ItemData) <= 1e-09 for ItemData in Cross)


def HasBoxFaces(
    DocData: CadDocument, LengthValue: float, WidthValue: float, HeightValue: float
) -> bool:
    BrepData = DocData.brep
    if (
        BrepData is None
        or len(BrepData.curves) != 12
        or len(BrepData.surfaces) != 6
        or (not BrepData.regions[0].solid)
    ):
        return False
    if not all(
        (
            isinstance(ItemData, LineCurve) and IsAxisLine(ItemData.direction)
            for ItemData in BrepData.curves
        )
    ) or any((not IsIdentity(ItemData.transform) for ItemData in BrepData.bodies)):
        return False
    VertexById = {ItemData.id: ItemData.point for ItemData in BrepData.vertices}
    CurveById = {ItemData.id: ItemData for ItemData in BrepData.curves}
    for EdgeValue in BrepData.edges:
        CurveValue = CurveById.get(EdgeValue.curve_id)
        StartValue = VertexById.get(EdgeValue.start_vertex_id)
        EndValue = VertexById.get(EdgeValue.end_vertex_id)
        if (
            not isinstance(CurveValue, LineCurve)
            or StartValue is None
            or EndValue is None
            or (not IsOnLine(CurveValue, StartValue))
            or (not IsOnLine(CurveValue, EndValue))
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
        Offsets[AxisValue].append(OriginValue[AxisValue])
    return (
        IsOffsetPair(Offsets[0], LengthValue)
        and IsOffsetPair(Offsets[1], WidthValue)
        and IsOffsetPair(Offsets[2], HeightValue)
    )


def IsOffsetPair(Values: list[float], Expected: float) -> bool:
    if len(Values) != 2:
        return False
    LeftValue, RightValue = sorted(Values)
    return MathValue.isclose(
        LeftValue, 0.0, rel_tol=0.0, abs_tol=1e-09
    ) and MathValue.isclose(RightValue, Expected, rel_tol=0.0, abs_tol=1e-09)
