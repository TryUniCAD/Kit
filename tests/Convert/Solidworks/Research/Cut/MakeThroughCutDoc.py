from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# through cut regressions require independently authored portable owners before any native graph can be generated
def MakeThruCutDoc(AxisValue: str, Reverse: bool, BothEnds: bool) -> CadDocument:
    BaseModel = MakePlainDoc("GeneratedThroughCut", 61.0, 39.0, 14.3)
    Frame = PrincipalFrame(AxisValue)
    Plane = ReplaceValue(
        BaseModel.support_planes[0],
        name={"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"}[AxisValue],
        transform=Transform(
            SpaceVector(*Frame.OriginValue),
            SpaceVector(*Frame.AxisU),
            SpaceVector(*Frame.AxisV),
            SpaceVector(*Frame.NormalValue),
        ),
    )
    SketchValue = BaseModel.sketches[0]
    Points = ((-28.0, -18.0), (33.0, -18.0), (33.0, 21.0), (-28.0, 21.0))
    Lines = tuple(
        ReplaceValue(
            Entity,
            geometry=LineGeometry(
                PlaneVector(*Points[Index]), PlaneVector(*Points[(Index + 1) % 4])
            ),
        )
        for Index, Entity in enumerate(SketchValue.entities)
    )
    Relations = tuple(
        SketchRelation(
            "constraint/axis/" + Entity.id,
            KindValue,
            (ConstraintRef(Entity.id),),
        )
        for Entity, KindValue in zip(
            Lines, ("horizontal", "vertical", "horizontal", "vertical"), strict=True
        )
    )
    Stock = ReplaceValue(
        SketchValue, name="StockProfile", entities=Lines, constraints=Relations
    )
    BossFeature = ReplaceValue(
        BaseModel.feature_timeline[0],
        name="StockBoss",
        definition=ExtrudeFeature(
            BaseModel.parameters[0].value,
            ExtrudeEnd.KMidPlane,
            symmetric=True,
        ),
    )
    Circle = SketchEntity(
        "entity/circle",
        GeometryKind.KCircle,
        CircleGeometry(PlaneVector(11.8, 5.7), 3.1),
    )
    Profile = Sketch(
        "sketch/through",
        "ThroughProfile",
        Plane.id,
        (Circle,),
        closed_profile_entity_ids=((Circle.id,),),
    )
    CutFeature = FeatureStep(
        "feature/through",
        "ThroughFeature",
        FeatureKind.KExtrusion,
        1,
        input_feature_ids=(BossFeature.id,),
        sketch_id=Profile.id,
        operation=BooleanOp.KCutOperation,
        definition=ExtrudeFeature(
            end_condition=ExtrudeEnd.KThroughAll,
            reversed=Reverse,
            second_end_condition=ExtrudeEnd.KThroughAll if BothEnds else None,
        ),
    )
    return ReplaceValue(
        BaseModel,
        configurations=(ReplaceValue(BaseModel.configurations[0], name="Default"),),
        support_planes=(Plane,),
        sketches=(Stock, Profile),
        feature_timeline=(BossFeature, CutFeature),
        bodies=(
            ReplaceValue(
                BaseModel.bodies[0],
                name=BossFeature.name,
                final_feature_id=CutFeature.id,
            ),
        ),
    )
