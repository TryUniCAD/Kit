from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue


# field guards must use current modeled counts and the exact native enum or mask comparison
def IsFieldBranch(ScopeValue: FieldScope, RuleValue: NativeField) -> bool:
    Value = ReadScopeValue(ScopeValue, RuleValue.NameValue)
    if RuleValue.ModeValue == "Nonzero":
        return Value != 0
    if RuleValue.ModeValue == "Equals":
        return Value == RuleValue.MaskValue
    if RuleValue.ModeValue == "NotEquals":
        return Value != RuleValue.MaskValue
    if RuleValue.ModeValue == "Greater":
        return CastValue(int, Value) > RuleValue.MaskValue
    if RuleValue.ModeValue == "BitsEqual":
        return CastValue(int, Value) & RuleValue.MaskValue == RuleValue.CompareValue
    raise ValueError(f"unsupported native field guard {RuleValue.ModeValue}")
