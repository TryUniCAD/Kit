from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridKnots import (
    FlipKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsCurve import NubsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface


def GridBounds(
    Surface: NubsSurface, Width: int, Height: int
) -> tuple[NubsCurve, NubsCurve, NubsCurve, NubsCurve]:
    Points = Surface.Points
    if Width * Height != len(Points):
        raise ValueError("Fusion grid conversion has an unexpected pole count")
    Bottom = Points[:Width]
    Right = Points[Width - 1 :: Width]
    Top = tuple(reversed(Points[-Width:]))
    Left = tuple(reversed(Points[::Width]))
    return (
        NubsCurve(3, 0, Surface.KnotsU, Bottom),
        NubsCurve(3, 0, Surface.KnotsV, Right),
        NubsCurve(3, 0, FlipKnots(Surface.KnotsU), Top),
        NubsCurve(3, 0, FlipKnots(Surface.KnotsV), Left),
    )
