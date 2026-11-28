from dataclasses import replace as ReplaceValue
from typing import TypeAlias

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# a reserved saved branch matches either an actual field name or its complete branch expression
KSwChoice: TypeAlias = str | tuple[object, ...]


# only explicit ordinary refusals may be replaced inside the separate saved sweep context
def SwapSwBodyMut(
    FieldsValue: tuple[NativeField, ...],
    Choices: dict[KSwChoice, tuple[NativeField, ...]],
) -> tuple[NativeField, ...]:
    Values: list[NativeField] = []
    for FieldValue in FieldsValue:
        Choice = FieldValue.NameValue or FieldValue.ExpressionValue
        BodyValue = FieldValue.BodyValue
        if Choice in Choices:
            if len(BodyValue) != 1 or BodyValue[0].KindValue != "Fail":
                raise BodyUnsupported(
                    "saved sweep choice no longer has its ordinary refusal"
                )
            BodyValue = Choices.pop(Choice)
        elif BodyValue:
            BodyValue = SwapSwBodyMut(BodyValue, Choices)
        OtherValue = FieldValue.OtherValue
        if OtherValue:
            OtherValue = SwapSwBodyMut(OtherValue, Choices)
        Values.append(
            ReplaceValue(FieldValue, BodyValue=BodyValue, OtherValue=OtherValue)
        )
    return tuple(Values)
