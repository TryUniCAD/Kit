from dataclasses import fields as DataFields
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase
from typing import Protocol, cast as CastValue

from convert.adapters.Fusion.State.StateTypes import KStateNames


class RecordMaker(Protocol):
    def __call__(self, **Values: object) -> object:
        raise TypeError("a concrete semantic-state constructor is required")


def DecodeRecord(NameValue: object, Values: dict[str, object]) -> object:
    if not isinstance(NameValue, str) or NameValue not in KStateNames:
        raise ValueError("Unknown Fusion semantic-state record")
    ClassType = KStateNames[NameValue]
    if not IsDataClass(ClassType) or set(Values) != {
        Field.name for Field in DataFields(ClassType)
    }:
        raise ValueError("Fusion semantic-state record fields disagree")
    return CastValue(RecordMaker, ClassType)(**Values)


def DecodeEnum(NameValue: object, Value: object) -> object:
    if not isinstance(NameValue, str) or NameValue not in KStateNames:
        raise ValueError("Unknown Fusion semantic-state enum")
    ClassType = KStateNames[NameValue]
    if not issubclass(ClassType, EnumBase):
        raise ValueError("Fusion semantic-state enum type disagrees")
    return ClassType(Value)
