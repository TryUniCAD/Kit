from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import (
    PatPresentInput,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.ReadPatLook import (
    ReadPatLook,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.ReadPatStk import (
    ReadPatSketch,
    ReadPatStk,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureBoundPlane import BoundDatum
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureKinds import LinearPattern
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Records.RecordParameter import ParameterValue
from interchange.Records.RecordTopology import TopologyCounts
from interchange.document.Models.DocumentModel import CadDocument


# native provenance only qualifies a readback after a full comparison against the freshly constructed archive
def ColdPatInput(
    Document: CadDocument, NameValue: str
) -> tuple[CadDocument, PatPresentInput]:
    if (
        Document.assembly is not None
        or Document.brep_payloads
        or Document.meshes
        or Document.materials
    ):
        raise ValueError("cold pattern has another carried source domain")
    StepsValue = tuple(
        Value
        for Value in Document.feature_timeline
        if isinstance(
            Value.definition, (ExtrudeFeature, PlaneAxis, BoundDatum, LinearPattern)
        )
    )
    Plate, SeedOwner, Hinge, Angle, Pattern = StepsValue
    PlateSketch, SeedSketch = Document.sketches
    (ConfigValue,) = Document.configurations
    (BodyValue,) = Document.bodies
    Params = {Value.id: Value for Value in Document.parameters}
    (PlateDepth,) = Plate.parameter_ids
    (SeedDepth,) = SeedOwner.parameter_ids
    AngleId, OffsetId = Angle.parameter_ids
    CountId, PitchId = Pattern.parameter_ids
    PlateStep, PlateParam = ReadPatStk(Plate, Params[PlateDepth], PlateSketch, (), 0)
    SeedStep, SeedParam = ReadPatStk(
        SeedOwner, Params[SeedDepth], SeedSketch, (Plate.id,), 1
    )
    Definition = Pattern.definition
    if (
        type(Definition) is not LinearPattern
        or Params[PitchId].value != Definition.spacing
    ):
        raise ValueError("cold pattern spacing differs from its typed editable owner")
    PitchValue = ParameterValue(
        RequireScalar(Params[PitchId].attributes.get("native_value")),
        ValueKind.KLength,
        "m",
    )
    StepsValue = (
        PlateStep,
        SeedStep,
        ReplaceValue(Hinge, order=2, input_feature_ids=()),
        ReplaceValue(Angle, order=3, input_feature_ids=(Hinge.id,)),
        ReplaceValue(
            Pattern, order=4, definition=ReplaceValue(Definition, spacing=PitchValue)
        ),
    )
    ParamValues = (
        PlateParam,
        SeedParam,
        Params[AngleId],
        Params[OffsetId],
        Params[CountId],
        ReplaceValue(Params[PitchId], value=PitchValue),
    )
    if set(Params) != {Value.id for Value in ParamValues}:
        raise ValueError("cold pattern has another parameter owner")
    ResultValue = ReplaceValue(
        Document,
        source=ReplaceValue(Document.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(ConfigValue, attributes=FreezeMapping()),),
        parameters=tuple(
            ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
            for Value in ParamValues
        ),
        support_planes=tuple(
            ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
            for Value in Document.support_planes
        ),
        sketches=(ReadPatSketch(PlateSketch), ReadPatSketch(SeedSketch)),
        selections=tuple(
            ReplaceValue(
                Value,
                provenance=None,
                attributes=FreezeMapping(),
                query=FreezeMapping(),
            )
            for Value in Document.selections
        ),
        feature_timeline=tuple(
            ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
            for Value in StepsValue
        ),
        bodies=(
            ReplaceValue(
                BodyValue,
                provenance=None,
                attributes=FreezeMapping(),
                topology=TopologyCounts(),
            ),
        ),
        brep=None,
        diagnostics=(),
        metadata=FreezeMapping({"name": NameValue}),
        capabilities=frozenset(),
    )
    return ResultValue, ReadPatLook(Document, AngleId, CountId, PitchId)
