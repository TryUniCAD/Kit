from math import hypot as Hypot, isfinite as IsFinite

from convert.Geometry.Extrude.Polygon.DraftMass import DraftMass
from convert.Geometry.Extrude.Polygon.DraftMoment import DraftMoment


# native mass caches must agree with independently integrated changing rectangular sections
def DraftMeasures(Width: float, Depth: float, Height: float, Slope: float) -> DraftMass:
    Volume = DraftMoment(Width, Depth, Height, Slope, 1, 1, 0)
    FirstZ = DraftMoment(Width, Depth, Height, Slope, 1, 1, 1)
    SecondZ = DraftMoment(Width, Depth, Height, Slope, 1, 1, 2)
    SecondX = (
        Width**2 * Volume / 4 + DraftMoment(Width, Depth, Height, Slope, 3, 1, 0) / 12
    )
    SecondY = (
        Depth**2 * Volume / 4 + DraftMoment(Width, Depth, Height, Slope, 1, 3, 0) / 12
    )
    Area = (
        Width * Depth
        + (Width + 2 * Slope * Height) * (Depth + 2 * Slope * Height)
        + 2 * Height * (Width + Depth + 2 * Slope * Height) * Hypot(1, Slope)
    )
    if Volume <= 0 or not all(
        IsFinite(Value) for Value in (Volume, FirstZ, SecondX, SecondY, SecondZ, Area)
    ):
        raise ValueError("Drafted rectangle moments exceed finite positive geometry")
    return DraftMass(
        Volume,
        Area,
        (Width / 2, Depth / 2, FirstZ / Volume),
        (SecondY + SecondZ, SecondX + SecondZ, SecondX + SecondY),
        (-Width * Depth * Volume / 4, -Width * FirstZ / 2, -Depth * FirstZ / 2),
    )
