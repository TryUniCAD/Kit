from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Adapter import KSourceFormatKey
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanThinWrite import (
    HasThinWrite,
)
from interchange.document.Models.DocumentModel import CadDocument


# typed revolve projections use full document regenerative verification in both read modes
def IsThinRead(DocumentValue: CadDocument) -> bool:
    return (
        DocumentValue.source.format_id == KPartFormatId
        and DocumentValue.source.container_version == "4"
        and DocumentValue.metadata.get(KSourceFormatKey) == KPartFormatId
        and DocumentValue.metadata.get("solidworks.typed_thin_revolve_semantics")
        is True
        and HasThinWrite(DocumentValue)
    )
