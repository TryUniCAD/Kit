from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc


# the disclosed neutral circle geometry can be rebuilt without reading a native fixture
def MakeCircleDoc() -> CadDocument:
    Document = MakePlainDoc(
        "SDK circle diameter beta", ((0.0, 0.0), (10.0, 0.0), (0.0, 10.0)), 17.825
    )
    (SketchValue,) = Document.sketches
    ArcId = "circle/analytic"
    RadialId = "parameter/radial"
    CircleValue = SketchEntity(
        ArcId, GeometryKind.KCircle, CircleGeometry(PlaneVector(7.125, -5.675), 11.475)
    )
    Relations = (
        SketchRelation("relation/center", "fixed", (ConstraintRef(ArcId, "center"),)),
        SketchRelation(
            "relation/radial", "diameter", (ConstraintRef(ArcId),), RadialId
        ),
    )
    RadialValue = Parameter(
        RadialId,
        "D1",
        ParameterValue(22.95, ValueKind.KLength, "mm"),
        ParameterRole.KDriving,
        owner_id=SketchValue.id,
    )
    return ReplaceValue(
        Document,
        sketches=(
            ReplaceValue(
                SketchValue,
                entities=(CircleValue,),
                constraints=Relations,
                parameter_ids=(RadialId,),
                closed_profile_entity_ids=((ArcId,),),
            ),
        ),
        parameters=(*Document.parameters, RadialValue),
    )
