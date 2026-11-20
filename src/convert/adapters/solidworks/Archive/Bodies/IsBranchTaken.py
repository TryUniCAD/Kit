from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue


# the native feature prefixes select their fields from the owning scope and archive flags
def IsBranchTaken(
    ContextValue: BodyContext, ScopeValue: FieldScope, RuleValue: NativeField
) -> bool:
    FlagsValue = ContextValue.FlagsValue
    Conditions = FlagsValue.get("conditions", 0)
    match RuleValue.ModeValue:
        case "Nonzero":
            return ReadScopeValue(ScopeValue, RuleValue.NameValue) != 0
        case "Condition":
            return bool(Conditions & RuleValue.MaskValue)
        case "NotContext":
            return not FlagsValue.get(RuleValue.NameValue, 0)
        case "ConditionsClear":
            return Conditions == 0
        case "PeNoise":
            return bool(
                (FlagsValue.get("pe_active", 0) and FlagsValue.get("pe_helper", 0))
                or FlagsValue.get("pe_file", 0)
            )
        case _:
            raise BodyUnsupported(
                f"unsupported native branch rule {RuleValue.ModeValue}"
            )
