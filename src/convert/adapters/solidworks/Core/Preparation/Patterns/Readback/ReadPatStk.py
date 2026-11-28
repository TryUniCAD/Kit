from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdSketch import (
    ReadColdSketch,
)
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch


# the shared line owner normalizes coordinates while validated unary relations remain portable
def ReadPatSketch(Original: Sketch) -> Sketch:
    return ReplaceValue(
        ReadColdSketch(Original),
        constraints=tuple(
            ReplaceValue(Value, provenance=None) for Value in Original.constraints
        ),
    )


# rebuild the actual two stock feature dependencies while removing only sketch inputs already separately owned
def ReadPatStk(
    Feature: FeatureStep,
    Driver: Parameter,
    SketchValue: Sketch,
    ParentIds: tuple[str, ...],
    Index: int,
) -> tuple[FeatureStep, Parameter]:
    (ProfileKey,) = tuple(
        Value for Value in Feature.input_feature_ids if Value not in ParentIds
    )
    if (
        Feature.sketch_id != SketchValue.id
        or Feature.input_feature_ids != (*ParentIds, ProfileKey)
        or len(Feature.selection_ids) != len(ParentIds)
    ):
        raise ValueError(
            "cold pattern readback stock lacks its distinct sketch or predecessor"
        )
    Definition = Feature.definition
    Depth = RequireScalar(Driver.attributes.get("native_value"))
    if (
        type(Definition) is not ExtrudeFeature
        or Feature.parameter_ids != (Driver.id,)
        or Driver.attributes.get("native_unit") != "m"
        or Driver.value != ParameterValue(Depth / 0.001, ValueKind.KLength, "mm")
        or Definition.length != Driver.value
    ):
        raise ValueError("cold pattern depth differs from its typed editable owner")
    DepthValue = ParameterValue(Depth, ValueKind.KLength, "m")
    return (
        ReplaceValue(
            Feature,
            order=Index,
            input_feature_ids=ParentIds,
            definition=ReplaceValue(Definition, length=DepthValue),
        ),
        ReplaceValue(Driver, value=DepthValue),
    )
