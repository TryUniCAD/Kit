from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# public circle acceptance needs independently authored portable intent without native files or research object graphs
def MakeWriteCircle(NameValue: str, IsTop: bool) -> CadDocument:
    RadiusValue = 9.625 if IsTop else 6.375
    CenterValue = (-2.75, 4.125) if IsTop else (5.875, -8.125)
    DocumentValue = MakePlainDoc(NameValue, 1.0, 1.0, 13.625)
    SketchValue = DocumentValue.sketches[0]
    CircleValue = SketchEntity(
        "circle/analytic",
        GeometryKind.KCircle,
        CircleGeometry(PlaneVector(*CenterValue), RadiusValue),
    )
    RadialValue = Parameter(
        "parameter/radial",
        "D1",
        ParameterValue(RadiusValue * (1 if IsTop else 2), ValueKind.KLength, "mm"),
        owner_id=SketchValue.id,
    )
    SketchValue = ReplaceValue(
        SketchValue,
        entities=(CircleValue,),
        parameter_ids=(RadialValue.id,),
        constraints=(
            SketchRelation(
                "relation/center", "fixed", (ConstraintRef(CircleValue.id, "center"),)
            ),
            SketchRelation(
                "relation/radial",
                "radius" if IsTop else "diameter",
                (ConstraintRef(CircleValue.id),),
                RadialValue.id,
            ),
        ),
        closed_profile_entity_ids=((CircleValue.id,),),
    )
    FeatureValue = DocumentValue.feature_timeline[0]
    DefinitionValue = FeatureValue.definition
    if not isinstance(DefinitionValue, ExtrudeFeature):
        raise AssertionError("authored circle fixture lost its boss definition")
    PlaneValue = DocumentValue.support_planes[0]
    if IsTop:
        PlaneValue = ReplaceValue(
            PlaneValue,
            name="Top Plane",
            transform=Transform(
                SpaceVector(0, 0, 0),
                SpaceVector(1, 0, 0),
                SpaceVector(0, 0, -1),
                SpaceVector(0, 1, 0),
            ),
        )
    return ReplaceValue(
        DocumentValue,
        configurations=(ReplaceValue(DocumentValue.configurations[0], name="Default"),),
        sketches=(SketchValue,),
        support_planes=(PlaneValue,),
        parameters=(*DocumentValue.parameters, RadialValue),
        feature_timeline=(
            ReplaceValue(
                FeatureValue,
                definition=ReplaceValue(DefinitionValue, reversed=IsTop),
            ),
        ),
    )
