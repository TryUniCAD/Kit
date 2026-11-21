from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.Sketch import Sketch


# a source centre point remains a real owner even when the shared circle constructor derives it from the same geometry
def ReadSourceCirc(
    DocumentValue: CadDocument, SketchValue: Sketch, UnitScale: float
) -> tuple[CircleInput, str, str]:
    if (
        len(SketchValue.entities) != 2
        or SketchValue.constraints
        or SketchValue.parameter_ids
        or SketchValue.suppressed
    ):
        raise ValueError(
            "source cut requires its actual free circle and distinct centre"
        )
    ArcsValue = tuple(
        Value
        for Value in SketchValue.entities
        if type(Value.geometry) is CircleGeometry
    )
    PointsValue = tuple(
        Value for Value in SketchValue.entities if type(Value.geometry) is PointGeometry
    )
    if len(ArcsValue) != 1 or len(PointsValue) != 1:
        raise ValueError("source cut circle or centre point is missing or ambiguous")
    ArcValue, PointValue = ArcsValue[0], PointsValue[0]
    Geometry, Center = ArcValue.geometry, PointValue.geometry
    if type(Geometry) is not CircleGeometry or type(Center) is not PointGeometry:
        raise ValueError("source circle owners have invalid concrete geometry")
    if (
        Center.point != Geometry.center
        or ArcValue.kind != "circle"
        or PointValue.kind != "point"
        or SketchValue.closed_profile_entity_ids != ((ArcValue.id,),)
        or any(Value.fixed or Value.construction for Value in SketchValue.entities)
    ):
        raise ValueError("source circle centre or contour ownership differs")
    Evidence = RequireRecord(
        DocumentValue.metadata.get("solidworks.typed_resolved_semantics")
    )
    FreeValues = Evidence.get("free_circle_profiles")
    if (
        not isinstance(FreeValues, (list, tuple))
        or SketchValue.attributes.get("native_object_id") not in FreeValues
    ):
        raise ValueError(
            "source circle lacks the independently qualified typed centre binding"
        )
    return (
        CircleInput(
            (Geometry.center.x * UnitScale, Geometry.center.y * UnitScale),
            Geometry.radius * UnitScale,
            19000,
        ),
        ArcValue.id,
        PointValue.id,
    )
