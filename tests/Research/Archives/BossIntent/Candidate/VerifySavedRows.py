from typing import cast as CastValue

from interchange.geometry.Models.Sketch import SketchRelation
from tests.Research.Archives.BossIntent.Candidate.CheckSavedOrder import CheckSavedOrder


# reader spans must independently attribute each persisted relation to its exact native record
def VerifySavedRows(
    SavedRows: tuple[SketchRelation, ...],
    Request: dict[str, object],
    SourceProof: dict[str, object],
) -> None:
    assert len(SavedRows) == 7
    CheckSavedOrder(Request["source_ordered_relations"], SavedRows)
    assert SourceProof["saved_relations"] == [RuleValue.id for RuleValue in SavedRows]
    Sources = CastValue(list[dict[str, object]], Request["source_relation_provenance"])
    assert len(Sources) == len(SavedRows)
    FirstSpans = CastValue(list[list[object]], Sources[0]["spans"])
    LastSpans = CastValue(list[list[object]], Sources[-1]["spans"])
    assert FirstSpans[0][:3] == ["Contents/Config-0-ResolvedFeatures", 7828, 55]
    assert LastSpans[0][:3] == ["Contents/Config-0-ResolvedFeatures", 7993, 73]
    for RuleValue, Observed in zip(SavedRows, Sources, strict=True):
        Proof = RuleValue.provenance
        assert Proof is not None and Proof.adapter == "solidworks.sldprt"
        assert Proof.native_id and Proof.spans
        assert (
            RuleValue.driving
            and not RuleValue.suppressed
            and not RuleValue.attributes.get("inferred")
        )
        assert Observed == {
            "id": RuleValue.id,
            "adapter": Proof.adapter,
            "native_id": Proof.native_id,
            "spans": [
                [
                    SpanValue.stream,
                    SpanValue.offset,
                    SpanValue.length,
                    SpanValue.record_kind,
                ]
                for SpanValue in Proof.spans
            ],
        }
