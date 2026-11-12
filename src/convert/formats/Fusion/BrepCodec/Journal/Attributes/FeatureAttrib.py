from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)

KFeatureLayouts: dict[str, int] = {"feature_data": 2, "thread_face_data": 6}


@MakeDataClass(frozen=True, slots=True)
class FeatureAttrib:
    Links: AttribLinks
    DataName: str
    FeatureTag: int
    Flags: int
    TypeCode: int
    Points: tuple[KJournalVector, ...] = ()
    TailCode: int | None = None
