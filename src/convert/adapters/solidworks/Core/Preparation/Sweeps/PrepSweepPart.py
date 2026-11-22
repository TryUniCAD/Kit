from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepPart import SweepPart
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import (
    BuildSweepPart,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.CheckSwRead import CheckSwRead
from convert.adapters.solidworks.Core.Preparation.Sweeps.PlanSwTarget import (
    PlanSwTarget,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.SwReadInput import IsSwReadback
from interchange.document.Models.DocumentModel import CadDocument


# production builds the complete candidate before either output route can write it
def PrepSweepPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> SweepPart:
    SettingsValue = CheckPartOpts(OptionsValue)
    Candidate = BuildSweepPart(
        PlanSwTarget(DocumentValue, TargetValue, WrittenAt, SettingsValue)
    )
    if IsSwReadback(DocumentValue):
        CheckSwRead(DocumentValue, Candidate.BytesValue)
    return Candidate
