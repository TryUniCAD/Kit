from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.Equations.PrepareEqPart import PrepareEqPart
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.Equations.HasEqIntent import HasEqIntent
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import (
    CheckColdRead,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.document.Models.DocumentModel import CadDocument


# native part preparation must construct its only recipe from the neutral model target policy and one writer event before output is touched
def PrepareNative(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    SettingsValue = CheckPartOpts(OptionsValue)
    IsReadback = IsColdRead(DocumentValue)
    InputValue = DocumentValue
    if IsReadback:
        FinalValue = SettingsValue.values.get("final_destination", TargetValue)
        if not isinstance(FinalValue, (str, FilePath)):
            raise ValueError(
                "unnamed native streams require an explicit final destination"
            )
        InputValue = ColdReadInput(DocumentValue, PureWindowsPath(FinalValue).stem)
    if HasEqIntent(InputValue):
        Candidate = PrepareEqPart(InputValue, TargetValue, WrittenAt, SettingsValue)
    else:
        PlanValue = PlanPartWrite(InputValue)
        RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
        Candidate = RunPartPrep(
            InputValue, TargetValue, PlanValue, RecipeValue, SettingsValue
        )
    if IsReadback:
        CheckColdRead(DocumentValue, Candidate.BytesValue)
    return Candidate
