from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.document.Models.DocumentModel import CadDocument


# a reopened cold conic retains the native scaffold and still must prove complete regeneration
def IsColdEllip(DocumentValue: CadDocument) -> bool:
    return IsColdRead(DocumentValue) and any(
        EntityValue.kind == GeometryKind.KEllipse
        for SketchValue in DocumentValue.sketches
        for EntityValue in SketchValue.entities
    )
