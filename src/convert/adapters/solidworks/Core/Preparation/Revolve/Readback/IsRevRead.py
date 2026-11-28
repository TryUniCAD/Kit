from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Adapter import KSourceFormatKey
from convert.adapters.solidworks.Core.Preparation.Revolve.HasRevWrite import HasRevWrite
from interchange.document.Models.DocumentModel import CadDocument


# typed revolve projections use full document regenerative verification in both read modes
def IsRevRead(DocumentValue: CadDocument) -> bool:
    Report = DocumentValue.metadata.get("solidworks.typed_revolve_semantics")
    if not isinstance(Report, Mapping):
        return False
    MeasuredValue = CastValue(Mapping[str, object], Report)
    return (
        DocumentValue.source.format_id == KPartFormatId
        and DocumentValue.source.container_version == "4"
        and DocumentValue.metadata.get(KSourceFormatKey) == KPartFormatId
        and MeasuredValue.get("status") == "projected"
        and MeasuredValue.get("typed_geometry_projection") is True
        and HasRevWrite(DocumentValue)
    )
