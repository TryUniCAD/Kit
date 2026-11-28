from collections import Counter
from collections.abc import Mapping
from typing import cast as CastValue

from interchange.geometry.Models.Sketch import Sketch


# public constraints must preserve actual unary owners and complete point distance subelements without inferred relation rows
def AssertAxisRead(SketchValue: Sketch) -> None:
    assert len(SketchValue.constraints) == 6
    assert Counter(RuleValue.kind for RuleValue in SketchValue.constraints) == {
        "horizontal": 2,
        "vertical": 2,
        "distance": 2,
    }
    EntityIds = {Entity.id for Entity in SketchValue.entities}
    for RuleValue in SketchValue.constraints:
        assert RuleValue.driving and not RuleValue.suppressed
        assert RuleValue.attributes.get("inferred") is not True
        OwnerValue = CastValue(
            Mapping[str, object], RuleValue.attributes["typed_archive_owner"]
        )
        assert OwnerValue["field_span"] is False
        assert RuleValue.provenance is not None
        assert RuleValue.provenance.spans[0].record_kind == "typed-archive-object"
        assert all(
            Reference.entity_id in EntityIds for Reference in RuleValue.references
        )
        if RuleValue.kind == "distance":
            assert OwnerValue["class"] == "sgPntPntDist"
            assert RuleValue.attributes["native_code"] == 1
            assert len(RuleValue.references) == 2
            assert (
                RuleValue.references[0].entity_id == RuleValue.references[1].entity_id
            )
            assert {Reference.point for Reference in RuleValue.references} == {
                "start",
                "end",
            }
            assert RuleValue.parameter_id in SketchValue.parameter_ids
        else:
            assert OwnerValue["class"] == "sgSketch"
            assert OwnerValue["embedded_array"] == "dims.log_g1"
            assert OwnerValue["embedded_class"] == "sgLogG1Dim"
            assert RuleValue.attributes["native_code"] == (
                4 if RuleValue.kind == "horizontal" else 5
            )
            assert (
                len(RuleValue.references) == 1 and RuleValue.references[0].point == ""
            )
            assert RuleValue.parameter_id is None
