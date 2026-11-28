from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Writing.AttachedBox.PrepareBoxOut import (
    PrepareBoxOut,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.ProveBoxSource import (
    ProveBoxSource,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from interchange.document.Models.DocumentModel import CadDocument


# actual native file publication follows the same pure verified plan as registry preflight
def EmitBoxMut(
    Document: CadDocument, TargetValue: KTargetType, OptionsValue: WriteOptions | None
) -> WriteResult:
    PlanValue = PrepareBoxOut(ProveBoxSource(Document), TargetValue, OptionsValue)
    return PublishMeasMut(
        TargetValue,
        PlanValue.PathValue,
        PlanValue.SettingsValue,
        PlanValue.Payload,
        PlanValue.EvidenceValue,
        PlanValue.Transfers,
    )
