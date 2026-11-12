from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue


@MakeDataClass(frozen=True, slots=True)
class ValueStruct:
    Fields: tuple[NamedValue, ...]
