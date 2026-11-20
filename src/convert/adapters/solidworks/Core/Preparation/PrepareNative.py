from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportCandidate import (
    ImportCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import (
    PrepareCircle,
)
from convert.adapters.solidworks.Core.Preparation.Equations.PrepareEqPart import (
    PrepareEqPart,
)
from convert.adapters.solidworks.Core.Preparation.Imports.PrepareImport import (
    PrepareImport,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from interchange.document.Models.DocumentModel import CadDocument


# native part preparation must construct its only recipe from the neutral model target policy and one writer event before output is touched
def PrepareNative(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate | ImportCandidate:
    if DocumentValue.brep is not None:
        return PrepareImport(
            DocumentValue, TargetValue, WrittenAt, CheckPartOpts(OptionsValue)
        )
    if any(Parameter.expression is not None for Parameter in DocumentValue.parameters):
        return PrepareEqPart(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    SettingsValue = CheckPartOpts(OptionsValue)
    try:
        PlanValue = PlanPartWrite(DocumentValue)
    except (TypeError, ValueError):
        return PrepareCircle(DocumentValue, TargetValue, WrittenAt, SettingsValue)
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    return RunPartPrep(
        DocumentValue, TargetValue, PlanValue, RecipeValue, SettingsValue
    )
