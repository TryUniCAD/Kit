from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch


# the native sketch must preserve the four authored unary relations without adding an axis anchor or an inferred driver
def CheckRevRules(SketchValue: Sketch) -> None:
    EntityValues = {Entity.id: Entity for Entity in SketchValue.entities}
    OrderValue = SketchValue.closed_profile_entity_ids[0]
    for IndexValue, RelationValue in enumerate(SketchValue.constraints):
        EntityValue = EntityValues[OrderValue[IndexValue]]
        Geometry = EntityValue.geometry
        if type(Geometry) is not LineGeometry:
            raise ValueError("revolve relation must retain its actual line owner")
        KindValue = "horizontal" if Geometry.start.y == Geometry.end.y else "vertical"
        if (
            RelationValue.kind != KindValue
            or len(RelationValue.references) != 1
            or RelationValue.references[0].entity_id != EntityValue.id
            or RelationValue.references[0].point != ""
            or RelationValue.parameter_id is not None
            or not RelationValue.driving
            or RelationValue.suppressed
            or RelationValue.attributes
        ):
            raise ValueError("revolve requires its actual contour axis relations")
