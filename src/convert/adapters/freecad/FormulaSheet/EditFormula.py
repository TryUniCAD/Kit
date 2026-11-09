# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping

from convert.adapters.freecad.FormulaSheet.FormulaClosure import CloseFormulas
from convert.adapters.freecad.FormulaSheet.FormulaPlans import (
    FormulaPlan,
    ReadFusionPlan,
)
from convert.geometry.Formula.Arithmetic import IsLiteralExpr, ReadFormula
from interchange.records.RecordParameter import Parameter


# the editable feature requires a proven dependency chain with writable literal inputs
def IsEditFormula(
    DepthId: str, TaperId: str | None, Parameters: Mapping[str, Parameter]
) -> bool:
    Aliases = {
        Identity: f"edit_parameter_{Index}" for Index, Identity in enumerate(Parameters)
    }
    Pending = [DepthId]
    Plans: dict[str, FormulaPlan] = {}
    while Pending:
        Identity = Pending.pop()
        if Identity in Plans:
            continue
        Param = Parameters.get(Identity)
        if Param is None or (Identity != DepthId and Param.owner_id):
            return False
        Expression = Param.expression
        if Expression is None or Expression.language != "fusion":
            return False
        PlanValue = ReadFusionPlan(Param, Parameters, Aliases)
        if PlanValue is None:
            return False
        if not PlanValue.References:
            Parsed = ReadFormula(Expression.source)
            if Parsed is None or not IsLiteralExpr(Parsed):
                return False
        Plans[Identity] = PlanValue
        Pending.extend(PlanValue.References)
    Expected = set(Plans)
    if TaperId is not None:
        Expected.add(TaperId)
    return (
        Expected == set(Parameters)
        and bool(Plans[DepthId].References)
        and DepthId in CloseFormulas(Plans)
    )
