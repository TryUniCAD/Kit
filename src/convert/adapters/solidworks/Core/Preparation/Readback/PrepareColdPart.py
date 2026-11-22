from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Equations.HasEqIntent import (
    HasEqIntent,
)
from convert.adapters.solidworks.Core.Preparation.Equations.PrepareEqPart import (
    PrepareEqPart,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import (
    CheckColdRead,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from interchange.document.Models.DocumentModel import CadDocument


# strict readback must reuse the exact ordinary constructor and compare all retained source fields
def PrepareColdPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None,
) -> PartCandidate:
    Settings = CheckPartOpts(OptionsValue)
    FinalValue = Settings.values.get("final_destination", TargetValue)
    if not isinstance(FinalValue, (str, FilePath)):
        raise ValueError("unnamed native streams require an explicit final destination")
    InputValue = ColdReadInput(DocumentValue, PureWindowsPath(FinalValue).stem)
    if HasEqIntent(InputValue):
        Candidate = PrepareEqPart(InputValue, TargetValue, WrittenAt, Settings)
    else:
        PlanValue = PlanPartWrite(InputValue)
        Candidate = RunPartPrep(
            InputValue,
            TargetValue,
            PlanValue,
            MakePartRecipe(PlanValue, WrittenAt),
            Settings,
        )
    CheckColdRead(DocumentValue, Candidate.BytesValue)
    return Candidate
