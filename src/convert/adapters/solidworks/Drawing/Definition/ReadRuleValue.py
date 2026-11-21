from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape


# value operations are limited to those present in the pinned drawing grammar
def ReadRuleValue(Operator: str, Operands: KRuleShape) -> object:
    match Operator, Operands:
        case "Eq", (LeftValue, RightValue):
            return LeftValue == RightValue
        case "NotEq", (LeftValue, RightValue):
            return LeftValue != RightValue
        case "Not", (Operand,):
            return not Operand
        case "int", (Operand,):
            return int(bool(Operand))
        case "empty_map", ():
            return {}
        case "lookup_or", (Owner, str(FieldName), DefaultValue) if isinstance(
            Owner, Mapping
        ):
            return CastValue(Mapping[object, object], Owner).get(
                FieldName, DefaultValue
            )
        case "lookup", (Owner, str(FieldName)) if isinstance(Owner, Mapping):
            return CastValue(Mapping[object, object], Owner)[FieldName]
        case "sequence", _:
            return Operands
        case "In", (Operand, SequenceValue):
            return Operand in CastValue(KRuleShape, SequenceValue)
        case "BitAnd", (int(LeftValue), int(RightValue)):
            return LeftValue & RightValue
        case "max", (int(LeftValue), int(RightValue)):
            return max(LeftValue, RightValue)
        case "GtE", (int(LeftValue), int(RightValue)):
            return LeftValue >= RightValue
        case _:
            raise ValueError(f"unsupported SOLIDWORKS drawing expression {Operator}")
