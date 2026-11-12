from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup


@MakeDataClass(frozen=True, slots=True)
class ValueObject:
    Groups: tuple[EntityGroup, ...]
