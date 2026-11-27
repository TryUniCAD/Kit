from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# malformed cache vectors must cross a real archive boundary without changing geometry
def ChangeDualMass(
    Cache: ValueObject[KEntityValue], FieldName: str, AxisName: str
) -> ValueObject[KEntityValue]:
    Groups: list[EntityGroup[KEntityValue]] = []
    for Group in Cache.Groups:
        Fields: list[NamedValue[KEntityValue]] = []
        for Field in Group.Fields:
            if Field.FieldName != FieldName:
                Fields.append(Field)
                continue
            Value = Field.Value
            if isinstance(Value, ValueStruct):
                Value = ReplaceData(
                    Value,
                    Fields=tuple(
                        (
                            ReplaceData(Member, Value=NumberValue(Member.Value) + 1.0)
                            if Member.FieldName == AxisName
                            else Member
                        )
                        for Member in Value.Fields
                    ),
                )
            else:
                Value = NumberValue(Value) + 1.0
            Fields.append(ReplaceData(Field, Value=Value))
        Groups.append(ReplaceData(Group, Fields=tuple(Fields)))
    return ReplaceData(Cache, Groups=tuple(Groups))
