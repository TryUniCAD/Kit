from typing import cast as CastValue

from convert.adapters.solidworks.Drawing.Definition.ConceptShapes import KConceptShapes
from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.HasReadBaseMut import HasReadBaseMut
from convert.adapters.solidworks.Drawing.Definition.HasBranchMut import HasBranchMut
from convert.adapters.solidworks.Drawing.Definition.HasFieldsMut import HasFieldsMut
from convert.adapters.solidworks.Drawing.Definition.HasRepeatMut import HasRepeatMut
from convert.adapters.solidworks.Drawing.Definition.HasVirtualMut import HasVirtualMut
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape


# method recursion must remain bounded across inline and map allocated records
def RunMethodMut(Scope: FieldScope, MethodName: str) -> None:
    Rules = KConceptShapes.get(MethodName)
    if Rules is None:
        raise ValueError(f"unqualified drawing method {MethodName}")
    State = Scope.Context
    if State.CallDepth >= 56:
        raise ValueError(
            "SOLIDWORKS drawing archive nesting exceeds the supported depth"
        )
    State.CallDepth += 1
    try:
        RunStepsMut(Scope, Rules)
    finally:
        State.CallDepth -= 1


# every declared field or branch must be understood before the cursor can advance
def RunStepsMut(Scope: FieldScope, Rules: KRuleShape) -> None:
    for RuleValue in Rules:
        Shape = CastValue(KRuleShape, RuleValue)
        if len(Shape) == 2 and Shape[0] == "reject":
            raise ValueError(
                f"unqualified drawing branch for {Scope.OwnerName}: {Shape[1]}"
            )
        if (
            HasFieldsMut(Scope, Shape)
            or HasReadBaseMut(Scope, Shape, RunMethodMut)
            or HasBranchMut(Scope, Shape, RunStepsMut)
            or HasRepeatMut(Scope, Shape, RunStepsMut)
            or HasVirtualMut(Scope, Shape, RunStepsMut, RunMethodMut)
        ):
            continue
        raise ValueError(f"unqualified drawing archive branch for {Scope.OwnerName}")
