from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.BuildTiltModel import (
    BuildTiltModel,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternDatum import (
    PatternDatum,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureKinds import NativeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import ParameterValue
from interchange.document.Models.DocumentModel import CadDocument


# each angular history update keeps the neutral identity of its actual native step
def BindTiltStep(
    Feature: FeatureStep,
    NodeValue: ArchiveNode,
    References: tuple[ArchiveNode, ArchiveNode],
) -> FeatureStep:
    NativeIds = tuple(NativeNodeId(Value) for Value in References)
    if (
        Feature.name != ReadNativeName(NodeValue)
        or Feature.kind != FeatureKind.KReference
        or not isinstance(Feature.definition, NativeFeature)
        or Feature.suppressed
        or Feature.configuration_states
    ):
        raise ValueError("angular datum lacks its actual neutral feature owner")
    return ReplaceValue(
        Feature,
        input_feature_ids=tuple(f"sldprt:feature:{Value}" for Value in NativeIds),
        attributes=FreezeMapping(
            {**Feature.attributes, "native_dependencies": NativeIds}
        ),
    )


# the native angular driver supplants the keyword guess and keeps its own parameter id
def ApplyTiltDoc(
    Document: CadDocument, LinkValue: NativeLink, DatumValue: PatternDatum
) -> CadDocument:
    TiltValue = DatumValue.TiltValue
    if TiltValue is None:
        return Document
    HingeId = f"sldprt:feature:{NativeNodeId(TiltValue.HingeValue)}"
    PlaneId = f"sldprt:feature:{NativeNodeId(DatumValue.PlaneValue)}"
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    Hinge, Plane = Steps[HingeId], Steps[PlaneId]
    DriverId = f"sldprt:parameter:{NativeNodeId(DatumValue.PlaneValue)}:D1"
    (DriverValue,) = tuple(
        Value for Value in Document.parameters if Value.owner_id == PlaneId
    )
    if (
        Hinge.parameter_ids
        or Plane.parameter_ids != (DriverId,)
        or DriverValue.id != DriverId
        or DriverValue.name != "D1"
        or DriverValue.role != ParameterRole.KDriving
        or DriverValue.expression is not None
    ):
        raise ValueError(
            "angular datum does not have a distinct local driving parameter"
        )
    ProofValue = {
        **NativeNodeSpan(LinkValue, TiltValue.DriverValue),
        "value_field": "f58",
        "dimension_id": TiltValue.Dimension.FieldsValue["f50"],
    }
    BoundAngle = ReplaceValue(
        DriverValue,
        value=ParameterValue(TiltValue.AngleValue, ValueKind.KAngle, "rad"),
        attributes=FreezeMapping(
            {
                **DriverValue.attributes,
                "native_value": TiltValue.AngleValue,
                "native_unit": "rad",
                "dimension_kind": "angle",
                "typed_archive_owner": ProofValue,
            }
        ),
        provenance=TypedProvenance(ProofValue, DriverId),
    )
    Projection = BuildTiltModel(
        Document,
        LinkValue,
        BindTiltStep(
            Hinge, TiltValue.HingeValue, (TiltValue.TopValue, TiltValue.RightValue)
        ),
        BindTiltStep(
            Plane, DatumValue.PlaneValue, (TiltValue.RightValue, TiltValue.HingeValue)
        ),
        DatumValue.PlaneValue,
        TiltValue,
        DriverId,
    )
    BoundSteps = {HingeId: Projection.HingeValue, PlaneId: Projection.PlaneValue}
    PreviousPicks = frozenset((*Hinge.selection_ids, *Plane.selection_ids))
    NewPickIds = {Value.id for Value in Projection.PicksValue}
    if any(
        NewPickIds.intersection(Value.selection_ids)
        or PreviousPicks.intersection(Value.selection_ids)
        for Value in Document.feature_timeline
        if Value.id not in BoundSteps
    ):
        raise ValueError("angular datum selection is shared with another feature")
    ResultValue = ReplaceValue(
        Document,
        feature_timeline=tuple(
            BoundSteps.get(Value.id, Value) for Value in Document.feature_timeline
        ),
        support_planes=tuple(
            Projection.SupportValue if Value.id == Projection.SupportValue.id else Value
            for Value in Document.support_planes
        ),
        selections=tuple(
            Value for Value in Document.selections if Value.id not in PreviousPicks
        )
        + Projection.PicksValue,
        parameters=tuple(
            BoundAngle if Value is DriverValue else Value
            for Value in Document.parameters
        )
        + (Projection.OffsetValue,),
    )
    ResultValue.assert_valid()
    return ResultValue
