from convert.adapters.solidworks.Container.Format import KAsmFormatId
from convert.adapters.solidworks.Core.Adapter import KSourceFormatKey
from interchange.document.Models.DocumentModel import CadDocument


# only the ordinary native assembly reader can request the complete reopened bundle comparison
def IsNestedRead(Document: CadDocument) -> bool:
    return (
        Document.assembly is not None
        and Document.source.format_id == KAsmFormatId
        and Document.source.container_version == "4"
        and Document.source.application_version == "19000"
        and Document.metadata.get(KSourceFormatKey) == KAsmFormatId
    )
