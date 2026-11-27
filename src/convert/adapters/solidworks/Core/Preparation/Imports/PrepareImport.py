from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportCandidate import (
    ImportCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBoxPart import (
    MakeBoxPart,
)
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.Imports.MakeImportLight import (
    MakeImportLight,
)
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import (
    PlanImportPart,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument


# geometry planning supplies all value input and the destination supplies the native name
def PrepareImport(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    SettingsValue: WriteOptions,
) -> ImportCandidate:
    FinalValue = SettingsValue.values.get("final_destination", TargetValue)
    if not isinstance(FinalValue, (str, FilePath)):
        raise ValueError("local solid import needs a final SLDPRT locator")
    PlanValue = PlanImportPart(DocumentValue, PureWindowsPath(FinalValue).stem)
    (ConfigValue,) = DocumentValue.configurations
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested local solid configuration is unavailable")
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    OutputValue = FinalPartPath(
        TargetValue, SettingsValue, RecipeValue.OutputValue, PlanValue.NameValue
    )
    RecipeValue = ReplaceValue(RecipeValue, OutputValue=OutputValue)
    CheckPartInput(DocumentValue, RecipeValue, PlanValue)
    return MakeBoxPart(
        RecipeValue,
        PlanValue,
        PlanValue.NodesValue,
        MakeImportLight(WrittenAt),
        OwnedBody=PlanValue.OwnedBody,
    )
