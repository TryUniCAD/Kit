from typing import cast as CastValue

from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.ReadOneField import ReadOneField
from convert.adapters.solidworks.Drawing.Definition.ReadRuleExpr import ReadRuleExpr
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleRunner
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape


# archive flags bind the owner before any optional drawing record is read
def HasBranchMut(
    Scope: FieldScope, Statement: KRuleShape, RunBody: KRuleRunner
) -> bool:
    match Statement:
        case ("if", Predicate, YesRules, NoRules):
            Chosen = YesRules if ReadRuleExpr(Predicate, Scope) else NoRules
            RunBody(Scope, CastValue(KRuleShape, Chosen))
        case ("present", str(FlagName), str(KindName), BodyValue):
            FlagValue = ReadOneField(Scope, KindName)
            Scope.Fields[FlagName] = FlagValue
            if FlagValue:
                RunBody(Scope, CastValue(KRuleShape, BodyValue))
        case ("condition", int(MaskValue), BodyValue):
            PriorValue = Scope.Context.Conditions
            Scope.Context.Conditions = PriorValue | MaskValue
            try:
                RunBody(Scope, CastValue(KRuleShape, BodyValue))
            finally:
                Scope.Context.Conditions = PriorValue
        case ("exclude_conditions", int(MaskValue)) if (
            not Scope.Context.Conditions & MaskValue
        ):
            return True
        case _:
            return False
    return True
