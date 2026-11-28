from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Core.Preparation.Ellipse.PlanEllipse import PlanEllipse
from convert.adapters.solidworks.Core.Preparation.Ellipse.ReadEllipPos import (
    ReadEllipPos,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdBoss import (
    ReadColdBoss,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# readback construction extracts only actual support sketch boss and dimension owners from the verified document
def ReadEllipInput(
    Document: CadDocument, NameValue: str
) -> tuple[CadDocument, EllipsePlan]:
    Document.assert_valid()
    (SketchValue,) = Document.sketches
    (Entity,) = SketchValue.entities
    (BodyValue,) = Document.bodies
    (Config,) = Document.configurations
    (Driver,) = Document.parameters
    (PlaneValue,) = (
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
    )
    (BossValue,) = (
        Value
        for Value in Document.feature_timeline
        if Value.id == BodyValue.final_feature_id
    )
    (Profile,) = (
        Value
        for Value in Document.feature_timeline
        if Value.id in BossValue.input_feature_ids
    )
    if (
        BossValue.sketch_id != SketchValue.id
        or Profile.sketch_id != SketchValue.id
        or Driver.owner_id != BossValue.id
        or Driver.name != "D1"
    ):
        raise ValueError(
            "SOLIDWORKS ellipse readback lacks its actual sketch and D1 lineage"
        )
    Feature, Depth = ReadColdBoss(BossValue, Driver)
    InputValue = ReplaceValue(
        Document,
        source=ReplaceValue(Document.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(Config, attributes=FreezeMapping()),),
        parameters=(Depth,),
        support_planes=(
            ReplaceValue(PlaneValue, attributes=FreezeMapping(), provenance=None),
        ),
        sketches=(
            ReplaceValue(
                SketchValue,
                entities=(
                    ReplaceValue(Entity, attributes=FreezeMapping(), provenance=None),
                ),
                attributes=FreezeMapping(),
                provenance=None,
            ),
        ),
        feature_timeline=(Feature,),
        selections=(),
        bodies=(
            ReplaceValue(
                BodyValue,
                name=Feature.name,
                topology=TopologyCounts(),
                attributes=FreezeMapping(),
                provenance=None,
            ),
        ),
        diagnostics=(),
        metadata=FreezeMapping({"name": NameValue}),
        capabilities=frozenset(),
        brep=None,
    )
    PlanValue = PlanEllipse(InputValue)
    Center, Major, Minor = ReadEllipPos(Entity, PlanValue.DepthValue)
    return InputValue, ReplaceValue(
        PlanValue,
        CenterValue=Center,
        MajorValue=Major,
        MinorValue=Minor,
    )
