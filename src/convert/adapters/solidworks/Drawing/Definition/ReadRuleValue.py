from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape


# value operations are limited to those present in the pinned drawing grammar
def ReadRuleValue(Operator: str, Operands: KRuleShape) -> object:
    if Operator == "sequence":
        return Operands
    if Operator == "empty_map" and not Operands:
        return {}
    SizeValue = len(Operands)
    if SizeValue == 1 and Operator in ("Not", "int"):
        TruthValue = bool(Operands[0])
        return not TruthValue if Operator == "Not" else int(TruthValue)
    if SizeValue == 2:
        LeftValue, RightValue = Operands[0], Operands[1]
        if Operator in ("Eq", "NotEq"):
            return (
                LeftValue == RightValue if Operator == "Eq" else LeftValue != RightValue
            )
        if (
            Operator == "lookup"
            and isinstance(LeftValue, Mapping)
            and isinstance(RightValue, str)
        ):
            return CastValue(Mapping[object, object], LeftValue)[RightValue]
        if Operator == "In":
            return LeftValue in CastValue(KRuleShape, RightValue)
        if isinstance(LeftValue, int) and isinstance(RightValue, int):
            if Operator == "BitAnd":
                return LeftValue & RightValue
            if Operator == "max":
                return max(LeftValue, RightValue)
            if Operator == "GtE":
                return LeftValue >= RightValue
    if SizeValue == 3 and Operator == "lookup_or":
        Owner, FieldName, DefaultValue = Operands[0], Operands[1], Operands[2]
        if isinstance(Owner, Mapping) and isinstance(FieldName, str):
            return CastValue(Mapping[object, object], Owner).get(
                FieldName, DefaultValue
            )
    raise ValueError(f"unsupported SOLIDWORKS drawing expression {Operator}")
