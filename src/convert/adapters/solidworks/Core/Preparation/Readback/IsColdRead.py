from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Adapter import KSourceFormatKey
from interchange.document.Models.DocumentModel import CadDocument


# recorded native custody selects a strict comparison before any source projection is trusted
def HasColdSource(Document: CadDocument) -> bool:
    return (
        Document.source.format_id == KPartFormatId
        and Document.source.container_version == "4"
        and Document.metadata.get(KSourceFormatKey) == KPartFormatId
    )


# the ordinary line part readback requires its complete linked boundary
def IsColdRead(Document: CadDocument) -> bool:
    return HasColdSource(Document) and Document.brep is not None
