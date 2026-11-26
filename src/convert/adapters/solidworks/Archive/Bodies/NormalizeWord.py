from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# native runtime normalization must remain independent of the persisted source word
def NormalizeWord(
    ContextValue: BodyContext, RuleValue: NativeField, Value: object
) -> int:
    if RuleValue.ModeValue == "Zero":
        return 0
    if RuleValue.ModeValue == "AtomState":
        NumberValue = CastValue(int, Value)
        Conditions = ContextValue.FlagsValue.get("conditions", 0)
        return 0 if NumberValue > 1 and not (Conditions & 0x80) else NumberValue
    if RuleValue.ModeValue == "AtLeast":
        return max(CastValue(int, Value), RuleValue.MaskValue)
    if RuleValue.ModeValue == "Identity":
        return CastValue(int, Value)
    raise BodyUnsupported("unsupported native normalization rule")
