from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import (
    HasColdSource,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipPartRead import (
    KEllipseStations,
)
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.document.Models.DocumentModel import CadDocument


# a reopened cold conic retains the native scaffold and still must prove complete regeneration
def IsColdEllip(DocumentValue: CadDocument) -> bool:
    return HasColdSource(DocumentValue) and any(
        EntityValue.kind == GeometryKind.KEllipse
        and KEllipseStations in SketchValue.attributes
        for SketchValue in DocumentValue.sketches
        for EntityValue in SketchValue.entities
    )
