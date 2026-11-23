from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportCandidate import (
    ImportCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import (
    MakeBareImport,
)
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.Imports.ImportReadInput import (
    ImportReadInput,
)
from convert.adapters.solidworks.Core.Preparation.Imports.MakeImportLight import (
    MakeImportLight,
)
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import (
    PlanImportPart,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument


# a staged local import must carry the final filename and actual selected configuration
def PrepareImport(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    SettingsValue: WriteOptions,
) -> ImportCandidate:
    FinalValue = SettingsValue.values.get("final_destination")
    if FinalValue is None:
        FinalValue = TargetValue
    if not isinstance(FinalValue, (str, FilePath)):
        raise TypeError("final destination must be path text or a filesystem path")
    InputValue = ImportReadInput(DocumentValue)
    PlanValue = PlanImportPart(InputValue, FinalValue)
    (ConfigValue,) = DocumentValue.configurations
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested write configuration is unavailable")
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    OutputValue = FinalPartPath(
        TargetValue, SettingsValue, RecipeValue.OutputValue, PlanValue.NameValue
    )
    return MakeBareImport(
        InputValue,
        ReplaceValue(RecipeValue, OutputValue=OutputValue),
        PlanValue,
        AmbientValue=MakeImportLight(WrittenAt),
        OwnedBody=PlanValue.OwnedBody,
    )
