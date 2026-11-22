from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import CircleGeometry


# only the actual neutral outline can select the independent circle preparation
def IsCirclePart(DocumentValue: CadDocument) -> bool:
    return len(DocumentValue.sketches) == 1 and any(
        type(Entity.geometry) is CircleGeometry
        for Entity in DocumentValue.sketches[0].entities
    )
