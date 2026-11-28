from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepPart import SweepPart
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import (
    BuildSweepPart,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.PlanSwTarget import (
    PlanSwTarget,
)
from interchange.document.Models.DocumentModel import CadDocument


# production builds the complete candidate before either output route can write it
def PrepSweepPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> SweepPart:
    SettingsValue = CheckPartOpts(OptionsValue)
    return BuildSweepPart(
        PlanSwTarget(DocumentValue, TargetValue, WrittenAt, SettingsValue)
    )
