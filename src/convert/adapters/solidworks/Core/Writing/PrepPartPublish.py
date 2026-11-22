from collections.abc import Mapping

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Preparation.Revolve.HasRevWrite import HasRevWrite
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanThinWrite import (
    HasThinWrite,
)
from convert.adapters.solidworks.Core.Writing.Measured.MatchPartMeas import (
    MatchPartMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import ReadPartMeas
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.PrepRevPublish import (
    PrepRevPublish,
)
from convert.adapters.solidworks.Core.Writing.Measured.Thin.PrepThinPublish import (
    PrepThinPublish,
)
from interchange.document.Models.DocumentModel import CadDocument


# each supported part uses its own measurement authority before the shared publication step
def PrepPartPublish(
    DocumentValue: CadDocument, TargetValue: KTargetType, Settings: WriteOptions
) -> tuple[bytes, Mapping[str, object], bool]:
    if HasThinWrite(DocumentValue):
        return PrepThinPublish(DocumentValue, TargetValue, Settings)
    if HasRevWrite(DocumentValue):
        return PrepRevPublish(DocumentValue, TargetValue, Settings)
    WrittenAt, Receipt = ReadPartMeas(Settings)
    Payload = PrepareNative(DocumentValue, TargetValue, WrittenAt, Settings).BytesValue
    return Payload, MatchPartMeas(Receipt, Payload), IsColdRead(DocumentValue)
