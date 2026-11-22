from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Adapter import KSourceFormatKey
from interchange.document.Models.DocumentModel import CadDocument


# only the native typed reader projection requires regeneration and full source comparison
def IsColdRead(Document: CadDocument) -> bool:
    return (
        Document.source.format_id == KPartFormatId
        and Document.source.container_version == "4"
        and Document.metadata.get(KSourceFormatKey) == KPartFormatId
        and Document.brep is not None
    )
