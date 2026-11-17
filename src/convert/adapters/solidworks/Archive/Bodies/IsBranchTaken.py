from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.IsFieldBranch import IsFieldBranch
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Expressions.ExprFrame import ExprFrame
from convert.adapters.solidworks.Archive.Expressions.ReadExpression import (
    ReadExpression,
)


# field and mode guards must reproduce native branches without testing captured document rows
def IsBranchTaken(
    ContextValue: BodyContext,
    ScopeValue: FieldScope,
    NodeValue: ArchiveNode,
    RuleValue: NativeField,
) -> bool:
    if RuleValue.ModeValue == "Expression":
        return bool(
            ReadExpression(
                ExprFrame(ContextValue, ScopeValue, NodeValue),
                RuleValue.ExpressionValue,
            )
        )
    FlagsValue = ContextValue.FlagsValue
    if RuleValue.ModeValue in (
        "Nonzero",
        "Equals",
        "NotEquals",
        "Greater",
        "BitsEqual",
    ):
        return IsFieldBranch(ScopeValue, RuleValue)
    match RuleValue.ModeValue:
        case "Condition":
            return bool(FlagsValue.get("conditions", 0) & RuleValue.MaskValue)
        case "Context":
            return bool(FlagsValue.get(RuleValue.NameValue, 0))
        case "NotContext":
            return not FlagsValue.get(RuleValue.NameValue, 0)
        case "NotCondition":
            return not (FlagsValue.get("conditions", 0) & RuleValue.MaskValue)
        case "ConditionsClear":
            return FlagsValue.get("conditions", 0) == 0
        case "PeNoise":
            return bool(
                FlagsValue.get("pe_active", 0) and FlagsValue.get("pe_helper", 0)
            ) or bool(FlagsValue.get("pe_file", 0))
        case "Class":
            return NodeValue.ClassValue.NameValue == RuleValue.NameValue
        case "NotClass":
            return NodeValue.ClassValue.NameValue != RuleValue.NameValue
        case _:
            raise ValueError(f"unsupported native branch rule {RuleValue.ModeValue}")
