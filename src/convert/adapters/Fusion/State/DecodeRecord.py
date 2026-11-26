from dataclasses import fields as DataFields
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase
from typing import Protocol, cast as CastValue

from convert.adapters.Fusion.State.StateTypes import KStateNames
from convert.adapters.Fusion.State.StateDefaults import KStateDefaults
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Materialize import Materialize


# the record maker contract needs a dedicated boundary so public document claims remain grounded in native records
class RecordMaker(Protocol):

    # record maker needs an explicit validity boundary so public document claims remain grounded in native records
    def __call__(self, **Values: object) -> object:
        raise TypeError("a concrete semantic-state constructor is required")


# the record operation needs a distinct decoding boundary so public document claims remain grounded in native records
def DecodeRecord(NameValue: object, Values: dict[str, object]) -> object:
    if not isinstance(NameValue, str) or NameValue not in KStateNames:
        raise ValueError("Unknown Fusion semantic-state record")
    ClassType = KStateNames[NameValue]
    Values = {**KStateDefaults.get(NameValue, {}), **Values}
    if not IsDataClass(ClassType) or set(Values) != {
        Field.name for Field in DataFields(ClassType)
    }:
        raise ValueError("Fusion semantic-state record fields disagree")
    RecordValue = CastValue(RecordMaker, ClassType)(**Values)
    if isinstance(RecordValue, JournalModel):
        try:
            _ = Materialize(RecordValue)
        except (AttributeError, TypeError) as ErrorValue:
            raise ValueError("Malformed Fusion semantic-state journal") from ErrorValue
    return RecordValue


# the enum operation needs a distinct decoding boundary so public document claims remain grounded in native records
def DecodeEnum(NameValue: object, Value: object) -> object:
    if not isinstance(NameValue, str) or NameValue not in KStateNames:
        raise ValueError("Unknown Fusion semantic-state enum")
    ClassType = KStateNames[NameValue]
    if not issubclass(ClassType, EnumBase):
        raise ValueError("Fusion semantic-state enum type disagrees")
    return ClassType(Value)
