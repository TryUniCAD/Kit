from dataclasses import replace as ReplaceData
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.Formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# an independent point edit isolates presentation from the native parameter and operand records
def MoveDimPoint(
    Value: KEntityValue, CoordinateName: str
) -> ValueStruct[KEntityValue]:
    assert isinstance(Value, ValueStruct)
    return ReplaceData(
        Value,
        Fields=tuple(
            (
                ReplaceData(Field, Value=NumberValue(Field.Value) + 0.35)
                if Field.FieldName == CoordinateName
                else Field
            )
            for Field in Value.Fields
        ),
    )
