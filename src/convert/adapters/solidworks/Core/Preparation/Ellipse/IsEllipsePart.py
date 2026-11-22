from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind


# a full ellipse in a single extrusion requires its own checked profile constructor
def IsEllipsePart(DocumentValue: CadDocument) -> bool:
    Timeline = DocumentValue.feature_timeline
    return (
        len(Timeline) == 1
        and Timeline[0].kind == FeatureKind.KExtrusion
        and any(
            EntityValue.kind == GeometryKind.KEllipse
            for SketchValue in DocumentValue.sketches
            if SketchValue.id == Timeline[0].sketch_id
            for EntityValue in SketchValue.entities
        )
    )
