from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# runtime normalization must remain explicit while the independent wire word stays available
def NormalizeWord(
    ContextValue: BodyContext, RuleValue: NativeField, Value: object
) -> int:
    NumberValue = CastValue(int, Value)
    if RuleValue.ModeValue == "Zero":
        return 0
    if RuleValue.ModeValue == "AtLeast":
        return max(NumberValue, RuleValue.MaskValue)
    if RuleValue.ModeValue == "AtomState":
        return (
            0
            if not (ContextValue.FlagsValue.get("conditions", 0) & 0x80)
            and NumberValue > 1
            else NumberValue
        )
    if RuleValue.ModeValue == "Identity":
        return NumberValue
    if RuleValue.ModeValue == "Equals":
        return int(NumberValue == RuleValue.MaskValue)
    if RuleValue.ModeValue == "Positive":
        return int(NumberValue > 0)
    raise BodyUnsupported(
        f"unsupported native normalization rule {RuleValue.ModeValue}"
    )
