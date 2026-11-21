from dataclasses import replace as ReplaceValue

from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.VectorSpace import SpaceVector


# the neutral through direction carries the effective ray while native metadata retains the raw reversal bit
def WithColdCut(StepValue: FeatureStep, Direction: SpaceVector) -> FeatureStep:
    Definition = StepValue.definition
    if (
        not isinstance(Definition, ExtrudeFeature)
        or Definition.end_condition != ExtrudeEnd.KThroughAll
        or not Definition.reversed
    ):
        raise ValueError("cold cut lacks its actual through end during public binding")
    return ReplaceValue(
        StepValue,
        definition=ReplaceValue(Definition, direction=Direction, reversed=False),
    )
