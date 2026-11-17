from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# runtime normalization must remain explicit while the independent wire word stays available
def NormalizeWord(
    ContextValue: BodyContext, RuleValue: NativeField, Value: object
) -> int:
    NumberValue = CastValue(int, Value)
    match RuleValue.ModeValue:
        case "Zero":
            return 0
        case "AtLeast":
            return max(NumberValue, RuleValue.MaskValue)
        case "AtomState":
            return (
                0
                if not (ContextValue.FlagsValue.get("conditions", 0) & 0x80)
                and NumberValue > 1
                else NumberValue
            )
        case "Identity":
            return NumberValue
        case "Equals":
            return int(NumberValue == RuleValue.MaskValue)
        case "Positive":
            return int(NumberValue > 0)
        case _:
            raise ValueError(
                f"unsupported native normalization rule {RuleValue.ModeValue}"
            )
