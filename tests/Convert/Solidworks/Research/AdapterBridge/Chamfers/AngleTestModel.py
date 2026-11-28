from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureKinds import ChamferFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# an authored sharp corner supplies independent distance angle and physically ordered selections
def MakeAngleDoc() -> CadDocument:
    Model = MakePlainDoc("AngleArchive", 70.0, 47.5, 34.0)
    (Stock,) = Model.feature_timeline
    (BodyValue,) = Model.bodies
    StepId = "feature/bevel"
    Distance = Parameter(
        "parameter/distance",
        "D1",
        ParameterValue(3.375, ValueKind.KLength, "mm"),
        ParameterRole.KDriving,
        owner_id=StepId,
    )
    AngleValue = Parameter(
        "parameter/angle",
        "D2",
        ParameterValue(0.625, ValueKind.KAngle, "rad"),
        ParameterRole.KDriving,
        owner_id=StepId,
    )
    Picks = tuple(
        Selection(
            f"pick/{Suffix}",
            Stock.name + " " + Suffix,
            (SelectPathElem("feature", Stock.id, Suffix),),
            point=PointValue,
        )
        for Suffix, PointValue in (
            ("edge", SpaceVector(35.0, -23.75, 17.0)),
            ("distance face", SpaceVector(35.0, 0.0, 17.0)),
        )
    )
    Feature = FeatureStep(
        StepId,
        "EdgeChamfer",
        FeatureKind.KChamfer,
        1,
        (Stock.id,),
        parameter_ids=(Distance.id, AngleValue.id),
        definition=ChamferFeature(
            Distance.value, "distance_angle", angle=AngleValue.value
        ),
        selection_ids=tuple(Value.id for Value in Picks),
    )
    return ReplaceValue(
        Model,
        configurations=(ReplaceValue(Model.configurations[0], name="Default"),),
        parameters=(*Model.parameters, Distance, AngleValue),
        selections=Picks,
        feature_timeline=(Stock, Feature),
        bodies=(ReplaceValue(BodyValue, final_feature_id=Feature.id),),
    )
