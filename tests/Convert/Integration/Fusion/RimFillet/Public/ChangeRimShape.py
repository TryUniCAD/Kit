from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# profile and output corruptions keep real source history while challenging the bounded rim compatibility rule
def ChangeRimShape(Document: CadDocument, ModeName: str) -> CadDocument:
    Source, Feature = Document.feature_timeline[1:]
    Sketch = Document.sketches[0]
    Definition = Source.definition
    Fillet = Feature.definition
    assert isinstance(Definition, DistanceExtrude) and isinstance(Fillet, RadiusFillet)
    if ModeName == "missing_output":
        return ReplaceValue(
            Document,
            feature_timeline=(
                Document.feature_timeline[0],
                ReplaceValue(Source, OutputBodyIds=()),
                Feature,
            ),
        )
    if ModeName == "wrong_final":
        return ReplaceValue(
            Document,
            bodies=(ReplaceValue(Document.bodies[0], final_feature_id=Source.id),),
        )
    if ModeName == "wrong_frame":
        Plane = Document.support_planes[0]
        return ReplaceValue(
            Document,
            support_planes=(
                ReplaceValue(
                    Plane,
                    transform=ReplaceValue(
                        Plane.transform, origin=SpaceVector(1, 0, 0)
                    ),
                ),
            ),
        )
    if ModeName in ("reverse", "symmetric"):
        Changed = (
            ReplaceValue(Definition, Direction=SpaceVector(0, 0, -1))
            if ModeName == "reverse"
            else ReplaceValue(Definition, SideMode="symmetric_full")
        )
        return ReplaceValue(
            Document,
            feature_timeline=(
                Document.feature_timeline[0],
                ReplaceValue(Source, definition=Changed),
                Feature,
            ),
        )
    if ModeName in ("taper", "oversized_radius"):
        ProfileGeometry = next(
            Value.geometry
            for Value in Sketch.entities
            if isinstance(Value.geometry, CircleGeometry)
        )
        ParamId = (
            Definition.TaperParameterId
            if ModeName == "taper"
            else Fillet.RadiusParameterId
        )
        Amount = 0.1 if ModeName == "taper" else ProfileGeometry.radius
        return ReplaceValue(
            Document,
            parameters=tuple(
                (
                    ReplaceValue(Value, value=ReplaceValue(Value.value, value=Amount))
                    if Value.id == ParamId
                    else Value
                )
                for Value in Document.parameters
            ),
        )
    if ModeName == "missing_profile":
        return ReplaceValue(
            Document, sketches=(ReplaceValue(Sketch, closed_profile_entity_ids=()),)
        )
    if ModeName in ("line_profile", "offset_circle"):
        Circle = next(
            Value
            for Value in Sketch.entities
            if isinstance(Value.geometry, CircleGeometry)
        )
        assert isinstance(Circle.geometry, CircleGeometry)
        Geometry = (
            LineGeometry(PlaneVector(0, 0), PlaneVector(1, 0))
            if ModeName == "line_profile"
            else ReplaceValue(Circle.geometry, center=PlaneVector(1, 0))
        )
        ChangedEntity = ReplaceValue(
            Circle,
            geometry=Geometry,
            kind=(
                GeometryKind.KLine
                if ModeName == "line_profile"
                else GeometryKind.KCircle
            ),
        )
        return ReplaceValue(
            Document,
            sketches=(
                ReplaceValue(
                    Sketch,
                    entities=tuple(
                        ChangedEntity if Value.id == Circle.id else Value
                        for Value in Sketch.entities
                    ),
                ),
            ),
        )
    raise ValueError("Unknown neutral rim profile corruption")
