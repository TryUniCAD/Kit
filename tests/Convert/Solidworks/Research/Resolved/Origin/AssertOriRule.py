from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchRelation
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# a real coincidence must join the fixed external datum to the actual zero corner endpoint without asserting cross sketch object equality
def AssertOriRule(SketchValue: Sketch, RuleValue: SketchRelation) -> None:
    (PointValue,) = tuple(
        Entity for Entity in SketchValue.entities if Entity.kind == GeometryKind.KPoint
    )
    Entities = {Entity.id: Entity for Entity in SketchValue.entities}
    ExternalRef, LocalRef = RuleValue.references
    assert ExternalRef.entity_id == PointValue.id
    LocalValue = Entities[LocalRef.entity_id]
    assert isinstance(LocalValue.geometry, LineGeometry)
    assert LocalRef.point in ("start", "end")
    LocalPoint = (
        LocalValue.geometry.start
        if LocalRef.point == "start"
        else LocalValue.geometry.end
    )
    assert LocalPoint.x == LocalPoint.y == 0.0
    assert RuleValue.attributes["native_code"] == 9
    assert RuleValue.attributes["native_point_indices"] == (4, 0)
    assert RuleValue.attributes["native_origin_point_mark"] == 1
    assert RuleValue.attributes["origin_reference_freshness_checked"] is False
    assert (
        NativeRecord(PointValue.attributes["typed_archive_owner"])["embedded_array"]
        == "points"
    )
    assert (
        NativeRecord(RuleValue.attributes["typed_archive_owner"])["embedded_array"]
        == "dims.log_g2"
    )
    assert RuleValue.parameter_id is None
