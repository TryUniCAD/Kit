from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.NativeSourceKey import KSourceFormatKey
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import CircleGeometry


# only the cache free typed circle projection can select complete regenerated source comparison
def IsCircRead(Document: CadDocument) -> bool:
    if (
        Document.assembly is not None
        or Document.DrawingValue is not None
        or Document.source.format_id != KPartFormatId
        or Document.source.container_version != "4"
        or Document.metadata.get(KSourceFormatKey) != KPartFormatId
        or Document.brep_payloads
        or len(Document.sketches) != 1
        or len(Document.sketches[0].entities) != 2
    ):
        return False
    Entity = Document.sketches[0].entities[0]
    return (
        type(Entity.geometry) is CircleGeometry
        and "native_center_m" in Entity.attributes
    )
