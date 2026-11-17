from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.Drawing.DrawingWriter import DrawingWriter
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments


# drawing output must preserve its domain before a destination can be created
def CheckDrawWrites(DocumentValue: CadDocument, AdapterValue: CadWriterAdapter) -> None:
    if not any(
        ItemValue.DrawingValue is not None for ItemValue in WalkDocuments(DocumentValue)
    ):
        return
    if (
        not isinstance(AdapterValue, DrawingWriter)
        or AdapterValue.KTypedDrawings is not True
    ):
        raise ValueError(
            f"{AdapterValue.info.format_id} does not support typed drawings"
        )
