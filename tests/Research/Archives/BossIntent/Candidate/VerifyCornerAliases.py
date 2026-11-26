from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import ConstraintRef
from tests.Research.Archives.BossIntent.Candidate.VerifyOrigin import VerifyOrigin


# native corner aliases are separate from the external origin referenced by the saved coincidence
def VerifyCorners(
    Source: CadDocument, Target: CadDocument, SourceProof: dict[str, object]
) -> None:
    (SketchValue,), (TargetSketch,) = Source.sketches, Target.sketches
    (LoopEdges,) = SketchValue.closed_profile_entity_ids
    Entities = {Entity.id: Entity for Entity in SketchValue.entities}
    OriginId = VerifyOrigin(
        SketchValue, TargetSketch, Source.feature_timeline, LoopEdges[0]
    )
    TargetRules = {RuleValue.id: RuleValue for RuleValue in TargetSketch.constraints}
    Inferred = [
        RuleValue
        for RuleValue in SketchValue.constraints
        if RuleValue.attributes == {"inferred": True}
    ]
    assert len(Inferred) == len(LoopEdges) == 4
    assert SourceProof["inferred_join_ids"] == [RuleValue.id for RuleValue in Inferred]
    AliasIds: list[str] = []
    for Index, Following in enumerate(LoopEdges):
        Previous = LoopEdges[Index - 1]
        Shared = set(
            CastValue(
                tuple[int, ...], Entities[Previous].attributes["native_point_indices"]
            )
        )
        Shared.intersection_update(
            CastValue(
                tuple[int, ...], Entities[Following].attributes["native_point_indices"]
            )
        )
        (Alias,) = [
            Entity
            for Entity in SketchValue.entities
            if Entity.construction
            and not Entity.fixed
            and {CastValue(tuple[int, ...], Entity.attributes["native_point_id"])[0]}
            == Shared
        ]
        PreviousLine = Entities[Previous].geometry
        FollowingLine = Entities[Following].geometry
        assert isinstance(PreviousLine, LineGeometry) and isinstance(
            FollowingLine, LineGeometry
        )
        assert isinstance(Alias.geometry, PointGeometry)
        assert PreviousLine.end == FollowingLine.start == Alias.geometry.point
        AliasIds.append(Alias.id)
        RuleValue = Inferred[Index - 1]
        assert RuleValue.provenance is None and RuleValue.kind == "coincident"
        assert RuleValue.references == (
            ConstraintRef(Previous, "end"),
            ConstraintRef(Following, "start"),
        )
        assert (
            TargetRules[RuleValue.id].references == RuleValue.references
            and not TargetRules[RuleValue.id].attributes
        )
    assert SourceProof["shared_corner_aliases"] == AliasIds
    assert len(set(AliasIds)) == 4 and OriginId not in AliasIds
