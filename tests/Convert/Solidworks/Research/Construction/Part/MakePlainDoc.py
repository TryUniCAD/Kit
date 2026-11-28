from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


# complete candidate inputs must be actual independently authored neutral documents rather than research native objects or vendor files
def MakePlainDoc(
    NameValue: str, WidthValue: float, HeightValue: float, DepthValue: float
) -> CadDocument:
    VerticesValue = (
        (-WidthValue / 2, -HeightValue / 2),
        (WidthValue / 2, -HeightValue / 2),
        (WidthValue / 2, HeightValue / 2),
        (-WidthValue / 2, HeightValue / 2),
    )
    EntityIds = tuple(f"edge/{IndexValue}" for IndexValue in range(4))
    EntitiesValue = tuple(
        SketchEntity(
            EntityIds[IndexValue],
            GeometryKind.KLine,
            LineGeometry(
                PlaneVector(*VerticesValue[IndexValue]),
                PlaneVector(*VerticesValue[(IndexValue + 1) % 4]),
            ),
        )
        for IndexValue in range(4)
    )
    LengthValue = ParameterValue(DepthValue, ValueKind.KLength, "mm")
    SketchValue = Sketch(
        "sketch/profile",
        "Sketch1",
        "plane/front",
        EntitiesValue,
        closed_profile_entity_ids=(EntityIds,),
    )
    FeatureValue = FeatureStep(
        "feature/boss",
        "Boss-Extrude1",
        FeatureKind.KExtrusion,
        0,
        sketch_id=SketchValue.id,
        parameter_ids=("parameter/depth",),
        operation=BooleanOp.KCreate,
        definition=ExtrudeFeature(LengthValue, ExtrudeEnd.KBlind, False, False),
    )
    return CadDocument(
        CadSource("kit-neutral", "<authored-in-memory>", "0" * 64),
        (Configuration("configuration/default", "modeled default", True),),
        (
            Parameter(
                "parameter/depth",
                "D1",
                LengthValue,
                ParameterRole.KDriving,
                owner_id=FeatureValue.id,
            ),
        ),
        (SupportPlane("plane/front", "Front Plane", Transform()),),
        (SketchValue,),
        (),
        (FeatureValue,),
        (DesignBody("body/boss", FeatureValue.name, FeatureValue.id),),
        metadata={"name": NameValue},
        units=UnitSystem.KMillimeter,
    )
