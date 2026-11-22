from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.NativeSourceKey import KSourceFormatKey
from interchange.document.Models.DocumentModel import CadDocument


# only the native typed reader projection requires regeneration and full source comparison
def IsColdRead(Document: CadDocument) -> bool:
    return (
        Document.assembly is None
        and Document.DrawingValue is None
        and Document.source.format_id == KPartFormatId
        and Document.source.container_version == "4"
        and Document.metadata.get(KSourceFormatKey) == KPartFormatId
        and Document.brep is not None
    )
