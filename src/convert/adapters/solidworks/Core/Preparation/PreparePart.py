from typing import cast as CastValue
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import (
    ProjectPlain,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from interchange.document.Models.DocumentModel import CadDocument


# an unregistered adapter preparation boundary must compose only the exact supported neutral part without writing destinations or asserting native acceptance
def PreparePart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    RecipeValue: PartBuildInput,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    if type(CastValue(object, RecipeValue)) is not PartBuildInput:
        raise TypeError("plain part preparation requires an explicit typed recipe")
    SettingsValue = CheckPartOpts(OptionsValue)
    CheckPlainScope(DocumentValue)
    PlanValue = ProjectPlain(DocumentValue)
    return RunPartPrep(
        DocumentValue, TargetValue, PlanValue, RecipeValue, SettingsValue
    )
