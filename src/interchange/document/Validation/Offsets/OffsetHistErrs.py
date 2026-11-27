from typing import Mapping as TypeMap

from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Offsets.FaceOffset import FaceOffset


# modifying a face requires its body to come from one explicit earlier producer
def OffsetHistErrs(
    Feature: FeatureStep, Features: TypeMap[str, FeatureStep]
) -> tuple[str, ...]:
    Definition = Feature.definition
    if not isinstance(Definition, FaceOffset):
        return ()
    Producers = tuple(
        Features[Identity]
        for Identity in Feature.input_feature_ids
        if Identity in Features
        and Definition.TargetBodyId in Features[Identity].OutputBodyIds
        and Features[Identity].order < Feature.order
    )
    if len(Producers) != 1:
        return (
            f"face offset {Feature.id} has no unique prior producer for its target body",
        )
    return ()
