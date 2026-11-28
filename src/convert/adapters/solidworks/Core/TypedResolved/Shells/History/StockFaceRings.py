from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellRings import (
    ShellCorner,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ShellStock import (
    ShellStock,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


# each historical wall key must use its actual sketch line and extrusion endpoints
def StockFaceRings(
    StockValue: ShellStock, Footprint: ShellFootprint
) -> dict[tuple[int, int], frozenset[int]]:
    Corners = Footprint.CornerPoints()[:8]
    Tolerance = Footprint.CornerTolerance()
    Result = {(40, 0): frozenset(range(4)), (40, 1): frozenset(range(4, 8))}
    LoopValue = StockValue.LoopValue
    for LineValue in LoopValue.LinesValue:
        Endpoints = tuple(
            LoopValue.PointsValue[IndexValue].PositionValue
            for IndexValue in (LineValue.StartValue, LineValue.EndValue)
        )
        Result[74, LineValue.PermanentId] = frozenset(
            ShellCorner(SpaceVector(*PointValue, Height), Corners, Tolerance)
            for PointValue in Endpoints
            for Height in (Footprint.Bounds.minimum.z, Footprint.Bounds.maximum.z)
        )
    return Result
