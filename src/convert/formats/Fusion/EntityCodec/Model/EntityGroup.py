from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue


@MakeDataClass(frozen=True, slots=True)
class EntityGroup:
    ClassGuid: str
    Fields: tuple[NamedValue, ...]
    Opaque: bytes | None = None
