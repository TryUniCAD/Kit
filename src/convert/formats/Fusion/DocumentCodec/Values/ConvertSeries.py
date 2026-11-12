from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadObject,
    ReadSeries,
)
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


def ConvertSeries(
    Value: object, Shape: WireType, Catalog: dict[str, NativeSchema]
) -> ValueSeries | ValueMap | ValuePair:
    from convert.formats.Fusion.DocumentCodec.Values.ConvertValue import ConvertValue

    if Shape.KindValue in ("sequence", "set", "fixed"):
        return ValueSeries(
            tuple(
                ConvertValue(Entry, Shape.Arguments[0], Catalog)
                for Entry in ReadSeries(Value)
            )
        )
    if Shape.KindValue == "pair":
        Fields = ReadObject(Value)
        if set(Fields) != {"first", "second"}:
            raise ValueError("Invalid authored pair fields")
        return ValuePair(
            ConvertValue(Fields["first"], Shape.Arguments[0], Catalog),
            ConvertValue(Fields["second"], Shape.Arguments[1], Catalog),
        )
    Entries: list[ValuePair] = []
    for Entry in ReadSeries(Value):
        Fields = ReadObject(Entry)
        if set(Fields) != {"key", "value"}:
            raise ValueError("Invalid authored map fields")
        Entries.append(
            ValuePair(
                ConvertValue(Fields["key"], Shape.Arguments[0], Catalog),
                ConvertValue(Fields["value"], Shape.Arguments[1], Catalog),
            )
        )
    return ValueMap(tuple(Entries))
