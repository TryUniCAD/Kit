from dataclasses import dataclass as DataClass
from typing import TypeAlias

# both authored front solids need the same ordered model space coordinates
KStockBounds: TypeAlias = tuple[tuple[float, float, float], tuple[float, float, float]]


# the stock and seed must retain each actual sketch and feature name
@DataClass(frozen=True, slots=True)
class FrontStockBox:
    SketchName: str
    FeatureName: str
    BoundsValue: KStockBounds
