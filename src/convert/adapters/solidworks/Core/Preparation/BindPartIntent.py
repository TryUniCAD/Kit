from dataclasses import replace as ReplaceValue
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PartPlan import (
    KPartPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from interchange.document.Models.DocumentModel import CadDocument


# neutral geometry configuration units and support names must override stale recipe projections while explicit presentation and provenance remain caller owned
def BindPartIntent(
    DocumentValue: CadDocument,
    PlanValue: KPartPlan,
    RecipeValue: PartBuildInput,
    OutputValue: SelfFileInput,
) -> PartBuildInput:
    if type(CastValue(object, RecipeValue)) is not PartBuildInput:
        raise TypeError("plain part preparation requires an explicit typed recipe")
    UnitName = str(DocumentValue.units)
    SystemsValue = {"mm": "mmgs", "m": "mks", "in": "ips"}
    DocumentUnits = UnitInput(
        UnitName,
        RecipeValue.DocumentUnits.AngleUnit,
        SystemsValue[UnitName],
        RecipeValue.DocumentUnits.DecimalPlaces,
    )
    SystemValue = ReplaceValue(
        RecipeValue.SystemValue,
        PlaneNames=tuple(
            (
                AxisValue,
                PlanValue.PlaneName if AxisValue == PlanValue.AxisValue else NameValue,
            )
            for AxisValue, NameValue in RecipeValue.SystemValue.PlaneNames
        ),
    )
    return ReplaceValue(
        RecipeValue,
        DocumentUnits=DocumentUnits,
        SystemValue=SystemValue,
        OutputValue=OutputValue,
    )
