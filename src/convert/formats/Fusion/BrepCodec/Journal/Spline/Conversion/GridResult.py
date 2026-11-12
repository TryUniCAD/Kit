from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsCurve import NubsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


@MakeDataClass(frozen=True, slots=True)
class GridResult:
    Surface: NubsSurface
    Patches: tuple[PatchCell, ...]
    Bounds: tuple[NubsCurve, NubsCurve, NubsCurve, NubsCurve]
    Corners: tuple[KJournalVector, KJournalVector, KJournalVector, KJournalVector]
