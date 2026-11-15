from __future__ import annotations

import math as MathValue

from interchange import CadDocument, LineCurve, PlaneSurface

from convert.adapters.solidworks.core.BrepIdentity import IsIdentity


def HasPolyBrep(
    DocData: CadDocument, Points: tuple[tuple[float, float], ...], DepthValue: float
) -> bool:
    BrepData = DocData.brep
    if BrepData is None:
        return True
    CountValue = len(Points)
    if (
        len(BrepData.vertices) != CountValue * 2
        or len(BrepData.edges) != CountValue * 3
        or len(BrepData.faces) != CountValue + 2
        or len(BrepData.regions) != 1
        or len(BrepData.bodies) != 1
        or len(BrepData.curves) != CountValue * 3
        or len(BrepData.surfaces) != CountValue + 2
        or (not BrepData.regions[0].solid)
    ):
        return False
    if not all(
        (isinstance(ItemData, LineCurve) for ItemData in BrepData.curves)
    ) or not all(
        (isinstance(ItemData, PlaneSurface) for ItemData in BrepData.surfaces)
    ):
        return False
    ExpectedData = {
        (PointData[0], PointData[1], HeightValue)
        for PointData in Points
        for HeightValue in (0.0, DepthValue)
    }
    ActualData = {
        (ItemData.point.x, ItemData.point.y, ItemData.point.z)
        for ItemData in BrepData.vertices
    }
    if len(ActualData) != len(ExpectedData):
        return False
    for ActualPoint in ActualData:
        if not any(
            (
                all(
                    (
                        MathValue.isclose(
                            ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-09
                        )
                        for ActualValue, ExpectedValue in zip(
                            ActualPoint, ExpectedPoint, strict=True
                        )
                    )
                )
                for ExpectedPoint in ExpectedData
            )
        ):
            return False
    return IsIdentity(BrepData.bodies[0].transform)
