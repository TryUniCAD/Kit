from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import Sketch


# contour points and closed profile membership must exclude the separate external construction datum
def AssertOriginGeo(SketchValue: Sketch, LengthValue: float, WidthValue: float) -> None:
    LinesValue = tuple(
        Entity for Entity in SketchValue.entities if Entity.kind == GeometryKind.KLine
    )
    PointsValue = tuple(
        Entity for Entity in SketchValue.entities if Entity.kind == GeometryKind.KPoint
    )
    assert len(SketchValue.entities) == 5 and len(LinesValue) == 4
    (PointValue,) = PointsValue
    assert PointValue.construction and PointValue.fixed
    assert isinstance(PointValue.geometry, PointGeometry)
    assert PointValue.geometry.point.x == PointValue.geometry.point.y == 0.0
    Coordinates: set[tuple[float, float]] = set()
    for Entity in LinesValue:
        assert not Entity.construction and not Entity.fixed
        assert isinstance(Entity.geometry, LineGeometry)
        for Position in (Entity.geometry.start, Entity.geometry.end):
            Coordinates.add((round(Position.x, 9), round(Position.y, 9)))
    assert Coordinates == {
        (0.0, 0.0),
        (round(LengthValue, 9), 0.0),
        (round(LengthValue, 9), round(WidthValue, 9)),
        (0.0, round(WidthValue, 9)),
    }
    (ProfileValue,) = SketchValue.closed_profile_entity_ids
    assert len(ProfileValue) == len(set(ProfileValue)) == 4
    assert set(ProfileValue) == {Entity.id for Entity in LinesValue}
    assert PointValue.id not in ProfileValue
    assert PointValue.provenance is not None
    assert PointValue.provenance.spans[0].record_kind == "typed-archive-object"
