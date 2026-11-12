from convert.formats.Fusion.DocumentCodec.Values.ConvertFields import ConvertFields
from convert.formats.Fusion.DocumentCodec.Values.ConvertGroups import ConvertGroups
from convert.formats.Fusion.DocumentCodec.Values.ConvertRef import ConvertRef
from convert.formats.Fusion.DocumentCodec.Values.ConvertSeries import ConvertSeries
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import ReadObject
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Tags.SketchFields import KSketchFields


def ConvertValue(
    Value: object, Shape: WireType, Catalog: dict[str, NativeSchema]
) -> KEntityValue:
    KindValue = Shape.KindValue
    if KindValue == "ref":
        return ConvertRef(Value)
    if KindValue == "optional":
        return (
            None
            if Value is None
            else OptionalValue(ConvertValue(Value, Shape.Arguments[0], Catalog))
        )
    if KindValue in ("sequence", "set", "fixed", "pair", "map"):
        return ConvertSeries(Value, Shape, Catalog)
    if KindValue == "struct":
        return ValueStruct(ConvertFields(Value, Shape.Members, Catalog))
    if KindValue == "sketch-tag":
        return ValueStruct(ConvertFields(Value, KSketchFields, Catalog))
    if KindValue == "object":
        return ValueObject(ConvertGroups(Value, Catalog))
    if KindValue == "matrix":
        if ReadObject(Value) != {"identity": True}:
            raise ValueError(
                "Only identity matrices are qualified for document authoring"
            )
        return MatrixValue(None)
    if KindValue != "unsupported" and isinstance(Value, (bool, int, float, str)):
        return Value
    raise ValueError("Unsupported authored semantic value")
