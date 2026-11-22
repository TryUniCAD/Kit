from math import dist as Distance, isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumOffset,
    KDatumVector,
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    KStockBounds,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.JoinSeedBounds import (
    JoinSeedBounds,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.ReadStockBox import (
    ReadStockBox,
)


# the verified single solid repeats interior noncontacting footprints in its actual signed plane direction
def MakePatBoxes(
    PlateValue: KStockBounds,
    SeedValue: KStockBounds,
    Direction: KDatumVector,
    PitchValue: float,
    CountValue: int,
) -> tuple[KStockBounds, ...]:
    PlateBounds = ReadStockBox(PlateValue)
    SeedBounds = ReadStockBox(SeedValue)
    _ = JoinSeedBounds(PlateBounds, SeedBounds)
    if (
        type(CountValue) is not int
        or not 2 <= CountValue <= 8
        or type(PitchValue) not in (int, float)
        or not IsFinite(PitchValue)
        or PitchValue <= 0.0
    ):
        raise ValueError(
            "ordinary local pattern requires an active positive pitch and two to eight instances"
        )
    if (
        len(CastValue(tuple[float, ...], Direction)) != 3
        or not all(type(Value) is float and IsFinite(Value) for Value in Direction)
        or Direction[2] != 0.0
        or abs(Distance(Direction, KHingeRoot) - 1.0) >= 1e-14
    ):
        raise ValueError(
            "local pattern must use the actual signed direction in the seed sketch plane"
        )
    Lower, Upper = PlateBounds
    First, LastValue = SeedBounds
    Boxes = tuple(
        (
            DatumOffset(First, Direction, PitchValue * Index),
            DatumOffset(LastValue, Direction, PitchValue * Index),
        )
        for Index in range(CountValue)
    )
    if any(
        not all(
            Lower[AxisIndex] < Start[AxisIndex] < Finish[AxisIndex] < Upper[AxisIndex]
            for AxisIndex in (0, 1)
        )
        for Start, Finish in Boxes
    ):
        raise ValueError(
            "patterned raised footprints must all be wholly interior to the plate"
        )
    if any(
        not any(
            max(Start[AxisIndex], OtherStart[AxisIndex])
            > min(Finish[AxisIndex], OtherEnd[AxisIndex])
            for AxisIndex in (0, 1)
        )
        for Index, (Start, Finish) in enumerate(Boxes)
        for OtherStart, OtherEnd in Boxes[:Index]
    ):
        raise ValueError("patterned raised footprints must remain strictly separated")
    return Boxes
