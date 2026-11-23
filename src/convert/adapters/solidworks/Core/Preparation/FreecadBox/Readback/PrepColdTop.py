from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanTopCorner import (
    PlanTopCorner,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Readback.ReadTopInput import (
    ReadTopInput,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import (
    CheckColdRead,
)
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from interchange.document.Models.DocumentModel import CadDocument


# anchored top readback regenerates the shared part and verifies every retained source field before returning a candidate
def PrepColdTop(
    Document: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None,
) -> PartCandidate:
    Settings = CheckPartOpts(OptionsValue)
    FinalValue = Settings.values.get("final_destination", TargetValue)
    if not isinstance(FinalValue, (str, FilePath)):
        raise ValueError(
            "unnamed Top corner streams require an explicit final destination"
        )
    NeutralValue = ReadTopInput(Document, PureWindowsPath(FinalValue).stem)
    TopValue = PlanTopCorner(NeutralValue)
    if TopValue is None:
        raise ValueError(
            "SOLIDWORKS cold readback requires the actual anchored Top profile"
        )
    Projected, PlanValue = TopValue
    Candidate = RunPartPrep(
        Projected,
        TargetValue,
        PlanValue,
        MakePartRecipe(PlanValue, WrittenAt),
        Settings,
        TopCorner=True,
    )
    CheckColdRead(Document, Candidate.BytesValue)
    return Candidate
