from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.ThinRevolve import ThinRevolve
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Convert.Solidworks.Research.AdapterBridge.Revolve.MakeRevCase import (
    MakeRevCase,
)


# independent open line and unequal wall values exercise the hosted thin vocabulary
def MakeThinCase() -> CadDocument:
    Document = MakeRevCase("HostedThin", "one_sided")
    (StepValue,) = Document.feature_timeline
    (SketchValue,) = Document.sketches
    (BodyValue,) = Document.bodies
    AngleValue = StepValue.definition
    assert isinstance(AngleValue, AngularRevolve)
    LineValue = SketchEntity(
        "line/open",
        GeometryKind.KLine,
        LineGeometry(PlaneVector(-3.0, -9.0), PlaneVector(-3.0, 15.0)),
    )
    WallsValue = tuple(
        Parameter(
            f"parameter/{NameValue}",
            NameValue,
            ParameterValue(LengthValue, ValueKind.KLength, "mm"),
            ParameterRole.KDriving,
            owner_id=StepValue.id,
        )
        for NameValue, LengthValue in (("D3", 2.75), ("D4", 5.5))
    )
    Drivers = (*Document.parameters, *WallsValue)
    Definition = ThinRevolve(
        AngleValue, "two_sided", WallsValue[0].id, WallsValue[1].id
    )
    Feature = ReplaceValue(
        StepValue,
        name="HostedThinBoss",
        definition=Definition,
        parameter_ids=tuple(Value.id for Value in Drivers),
    )
    return ReplaceValue(
        Document,
        parameters=Drivers,
        sketches=(
            ReplaceValue(
                SketchValue,
                entities=(LineValue, SketchValue.entities[-1]),
                constraints=(),
                closed_profile_entity_ids=(),
            ),
        ),
        feature_timeline=(Feature,),
        bodies=(ReplaceValue(BodyValue, name=Feature.name),),
    )
