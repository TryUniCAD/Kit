from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.Materials.MaterialWriter import MaterialScope, MaterialWriter
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments


# writer capability checks preserve physical assignments on supported formats
def CheckMatWrites(Document: CadDocument, Adapter: CadWriterAdapter) -> None:
    if not any(Value.materials for Value in WalkDocuments(Document)):
        return
    if (
        not isinstance(Adapter, MaterialWriter)
        or Adapter.TypedMaterials is not True
        or (isinstance(Adapter, MaterialScope) and not Adapter.SupportsMatDoc(Document))
    ):
        raise ValueError(
            f"{Adapter.info.format_id} does not support typed material density and color"
        )
