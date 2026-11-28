from dataclasses import dataclass as DataClass
from typing import TypeAlias

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)

# stock extents retain each ordered principal interval in model metres
KStockBounds: TypeAlias = tuple[
    tuple[float, float], tuple[float, float], tuple[float, float]
]


# resolved picks keep the actual signed stock geometry before archive allocation
@DataClass(frozen=True, slots=True)
class ChmfEdgePlan:
    BoundsValue: KStockBounds
    EdgeAxis: int
    DistanceAxis: int
    CornerBits: tuple[int, int, int]
    ShortSpan: float


# the chamfer keeps its sole predecessor and exact driving distance and angle roles
@DataClass(frozen=True, slots=True)
class ChmfPlan:
    StockValue: BlindPlan
    EdgeValue: ChmfEdgePlan
    FeatureName: str
    SetbackValue: float
    AngleValue: float | None
    OtherSetback: float | None = None
