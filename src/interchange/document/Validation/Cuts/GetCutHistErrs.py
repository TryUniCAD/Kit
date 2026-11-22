from typing import Mapping as TypeMap
from interchange.Features.Distance.DistanceCut import DistanceCut
from interchange.Features.FeatureStep import FeatureStep


# modifying bodies require a declared prior producer in the actual dependency chain
def GetCutHistErrs(
    Feature: FeatureStep, Features: TypeMap[str, FeatureStep]
) -> tuple[str, ...]:
    Definition = Feature.definition
    if not isinstance(Definition, DistanceCut):
        return ()
    if set(Feature.OutputBodyIds) != set(Definition.TargetBodyIds):
        return (f"distance cut {Feature.id} output bodies do not match its targets",)
    for Identity in Definition.TargetBodyIds:
        Producers = tuple(
            Features[InputId]
            for InputId in Feature.input_feature_ids
            if InputId in Features
            and Identity in Features[InputId].OutputBodyIds
            and Features[InputId].order < Feature.order
        )
        if len(Producers) != 1:
            return (
                f"distance cut {Feature.id} has no unique prior producer for target body {Identity}",
            )
    return ()
