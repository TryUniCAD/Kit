from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# archive condition changes govern later native fields rather than serialized model values
def ChangeFlagsMut(ContextValue: BodyContext, RuleValue: NativeField) -> None:
    FlagsValue = ContextValue.FlagsValue
    Current = FlagsValue.get(RuleValue.NameValue, 0)
    match RuleValue.ModeValue:
        case "Assign":
            FlagsValue[RuleValue.NameValue] = RuleValue.MaskValue
        case "Set":
            FlagsValue[RuleValue.NameValue] = Current | RuleValue.MaskValue
        case "Clear":
            FlagsValue[RuleValue.NameValue] = Current & ~RuleValue.MaskValue
        case _:
            raise ValueError(f"unsupported native context rule {RuleValue.ModeValue}")
