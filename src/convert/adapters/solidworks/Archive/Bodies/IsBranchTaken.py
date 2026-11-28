from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
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
    RuleValue: NativeField,
    NodeValue: ArchiveNode,
) -> bool:
    if RuleValue.ModeValue == "Expression" and RuleValue.ExpressionValue:
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
    if RuleValue.ModeValue == "Condition":
        return bool(FlagsValue.get("conditions", 0) & RuleValue.MaskValue)
    if RuleValue.ModeValue == "Context":
        return bool(FlagsValue.get(RuleValue.NameValue, 0))
    if RuleValue.ModeValue == "NotContext":
        return not FlagsValue.get(RuleValue.NameValue, 0)
    if RuleValue.ModeValue == "NotCondition":
        return not (FlagsValue.get("conditions", 0) & RuleValue.MaskValue)
    if RuleValue.ModeValue == "ConditionsClear":
        return FlagsValue.get("conditions", 0) == 0
    if RuleValue.ModeValue == "PeNoise":
        return bool(
            FlagsValue.get("pe_active", 0) and FlagsValue.get("pe_helper", 0)
        ) or bool(FlagsValue.get("pe_file", 0))
    if RuleValue.ModeValue == "Class":
        return NodeValue.ClassValue.NameValue == RuleValue.NameValue
    if RuleValue.ModeValue == "NotClass":
        return NodeValue.ClassValue.NameValue != RuleValue.NameValue
    raise BodyUnsupported(f"unsupported native branch rule {RuleValue.ModeValue}")
