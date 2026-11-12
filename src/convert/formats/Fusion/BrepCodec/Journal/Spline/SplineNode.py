from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf


@MakeDataClass(frozen=True, slots=True)
class SplineNode:
    Prefix: EntityPrefix
    Reversed: bool
    Surface: TsplineSurf | SubtypeRef
    ULower: float | None
    UUpper: float | None
    VLower: float | None
    VUpper: float | None
