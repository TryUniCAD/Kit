from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


@MakeDataClass(frozen=True, slots=True)
class NurbsEdge:
    StartVertex: int
    EndVertex: int
    Curve: BsCurve


@MakeDataClass(frozen=True, slots=True)
class NurbsUse:
    EdgeIndex: int
    Reversed: bool
    Pcurve: BsCurve


@MakeDataClass(frozen=True, slots=True)
class NurbsFace:
    Surface: BsSurface
    Uses: tuple[NurbsUse, ...]


@MakeDataClass(frozen=True, slots=True)
class NurbsBody:
    PointsCm: tuple[KJournalVector, ...]
    Edges: tuple[NurbsEdge, ...]
    Faces: tuple[NurbsFace, ...]
    EntityTag: int = -1
