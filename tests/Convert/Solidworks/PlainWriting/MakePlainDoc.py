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


# independent polygon models supply their own line endpoints and driving length at the writer boundary
def MakePlainDoc(
    NameValue: str, Corners: tuple[tuple[float, float], ...], DepthValue: float
) -> CadDocument:
    Points = tuple(PlaneVector(*Coords) for Coords in Corners)
    Entities = tuple(
        SketchEntity(
            f"edge/{IndexValue}", GeometryKind.KLine, LineGeometry(Start, Finish)
        )
        for IndexValue, (Start, Finish) in enumerate(
            zip(Points, Points[1:] + Points[:1], strict=True)
        )
    )
    SketchValue = Sketch(
        "sketch/profile",
        "Sketch1",
        "plane/front",
        Entities,
        closed_profile_entity_ids=(tuple(Entity.id for Entity in Entities),),
    )
    LengthValue = ParameterValue(DepthValue, ValueKind.KLength, "mm")
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
