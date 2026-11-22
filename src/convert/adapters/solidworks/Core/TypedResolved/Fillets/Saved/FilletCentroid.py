from math import pi as PiValue, prod as ProductValue


# the removed square outside the quarter circle has its own centroid and exact volume
def FilletCentroid(
    Bounds: tuple[tuple[float, float], ...],
    AxisIndex: int,
    Signs: tuple[int, ...],
    Radius: float,
) -> tuple[float, ...]:
    Sizes = tuple(Upper - Lower for Lower, Upper in Bounds)
    Center = tuple((Lower + Upper) * 0.5 for Lower, Upper in Bounds)
    CornerArea = 1.0 - PiValue / 4
    CutVolume = CornerArea * Radius * Radius * Sizes[AxisIndex]
    StockVolume = ProductValue(Sizes)
    Offset = Radius * (5.0 / 6.0 - PiValue / 4) / CornerArea
    CutCenter = list(Center)
    CrossAxes = tuple(Index for Index in range(3) if Index != AxisIndex)
    for Index, Sense in zip(CrossAxes, Signs, strict=True):
        Lower, Upper = Bounds[Index]
        Corner = Lower if Sense > 0 else Upper
        CutCenter[Index] = Corner + Sense * Offset
    return tuple(
        (Prior * StockVolume - Removed * CutVolume) * 1000.0 / (StockVolume - CutVolume)
        for Prior, Removed in zip(Center, CutCenter, strict=True)
    )
