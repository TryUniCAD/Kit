from re import fullmatch as FullMatch

from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, TextValue
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Expression, Parameter, ParameterValue


# unitless tangency weight must retain its driving role without widening length expression admission
def ProjectWeight(Value: NativeNode, Owner: NativeNode) -> Parameter:
    Literal = TextValue(Value.Fields["expression"])
    if (
        not FullMatch(r"\s*[+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\s*", Literal)
        or float(Literal) != NumberValue(Value.Fields["value"])
        or NumberValue(Value.Fields["value"]) != 1
    ):
        raise ValueError("Native rim tangency weight requires literal unitless one")
    return Parameter(
        Value.Identity,
        TextValue(Value.Fields["userName"]),
        ParameterValue(1, ValueKind.KNumber, ""),
        expression=Expression(Literal, language="fusion"),
        owner_id=Owner.Identity,
        attributes={
            "comment": TextValue(Value.Fields["comment"]),
            "native_name": "TangencyWeight",
        },
    )
