from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue


# field guards must use current modeled counts and the exact native enum or mask comparison
def IsFieldBranch(ScopeValue: FieldScope, RuleValue: NativeField) -> bool:
    Value = ReadScopeValue(ScopeValue, RuleValue.NameValue)
    match RuleValue.ModeValue:
        case "Nonzero":
            return Value != 0
        case "Equals":
            return Value == RuleValue.MaskValue
        case "NotEquals":
            return Value != RuleValue.MaskValue
        case "Greater":
            return CastValue(int, Value) > RuleValue.MaskValue
        case "BitsEqual":
            return CastValue(int, Value) & RuleValue.MaskValue == RuleValue.CompareValue
    raise ValueError(f"unsupported native field guard {RuleValue.ModeValue}")
