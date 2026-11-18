from collections import Counter

from interchange.geometry.Models.Sketch import Sketch
from tests.Convert.Solidworks.Research.Resolved.Origin.AssertOriRule import (
    AssertOriRule,
)


# all seven actual solver records must retain public reference ownership provenance and driving state
def AssertOriRules(SketchValue: Sketch) -> None:
    assert Counter(RuleValue.kind for RuleValue in SketchValue.constraints) == {
        "horizontal": 2,
        "vertical": 2,
        "distance": 2,
        "coincident": 1,
    }
    Entities = {Entity.id: Entity for Entity in SketchValue.entities}
    for RuleValue in SketchValue.constraints:
        assert RuleValue.driving and not RuleValue.suppressed
        assert RuleValue.attributes.get("inferred") is not True
        assert RuleValue.provenance is not None
        assert RuleValue.provenance.spans[0].record_kind == "typed-archive-object"
        assert all(
            Reference.entity_id in Entities for Reference in RuleValue.references
        )
        if RuleValue.kind == "coincident":
            AssertOriRule(SketchValue, RuleValue)
        elif RuleValue.kind == "distance":
            assert RuleValue.parameter_id in SketchValue.parameter_ids
            assert {Reference.point for Reference in RuleValue.references} == {
                "start",
                "end",
            }
            assert len({Reference.entity_id for Reference in RuleValue.references}) == 1
