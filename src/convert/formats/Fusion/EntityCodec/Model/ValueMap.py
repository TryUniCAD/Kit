from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


@MakeDataClass(frozen=True, slots=True)
class ValueMap:
    Entries: tuple[ValuePair, ...]
