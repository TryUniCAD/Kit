from typing import cast as CastValue

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
    ModeValue = RuleValue.ModeValue
    if ModeValue == "Nonzero":
        return ReadScopeValue(ScopeValue, RuleValue.NameValue) != 0
    if ModeValue == "Condition":
        return bool(Conditions & RuleValue.MaskValue)
    if ModeValue == "NotContext":
        return not FlagsValue.get(RuleValue.NameValue, 0)
    if ModeValue == "ConditionsClear":
        return Conditions == 0
    if ModeValue == "PeNoise":
        return bool(
            (FlagsValue.get("pe_active", 0) and FlagsValue.get("pe_helper", 0))
            or FlagsValue.get("pe_file", 0)
        )
    if ModeValue == "Equals":
        return ReadScopeValue(ScopeValue, RuleValue.NameValue) == RuleValue.MaskValue
    if ModeValue == "Greater":
        Value = CastValue(int, ReadScopeValue(ScopeValue, RuleValue.NameValue))
        return Value > RuleValue.MaskValue
    if ModeValue == "NotCondition":
        return not (Conditions & RuleValue.MaskValue)
    raise BodyUnsupported(f"unsupported native branch rule {ModeValue}")
