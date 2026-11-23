from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.document.Models.DocumentModel import CadDocument


# only complete native geometry with the linked top corner can select this readback
def IsTopRead(Document: CadDocument) -> bool:
    if Document.brep is None or not IsColdRead(Document) or len(Document.sketches) != 1:
        return False
    (SketchValue,) = Document.sketches
    return SketchValue.attributes.get("typed_origin_coincidence") is True and any(
        PlaneValue.id == SketchValue.support_plane_id and PlaneValue.name == "Top Plane"
        for PlaneValue in Document.support_planes
    )
