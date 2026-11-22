from typing import Mapping as TypeMap

from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.Features.Offsets.GetOffsetValue import GetOffsetValue
from interchange.geometry.Models.Selection import Selection
from interchange.Records.RecordParameter import Parameter


# offset definitions require live operands before any geometry consumer can trust their signed distance
def OffsetDefErrors(
    Feature: FeatureStep,
    Definition: FaceOffset,
    IdentitySets: TypeMap[str, set[str]],
    Parameters: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
) -> tuple[str, ...]:
    if Definition.TargetBodyId not in IdentitySets["bodies"]:
        return (f"face offset {Feature.id} references a missing target body",)
    try:
        _ = GetOffsetValue(Feature, Definition, Parameters, Selections)
    except ValueError as ErrorInfo:
        return (f"face offset {Feature.id} is invalid: {ErrorInfo}",)
    return ()
