from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.ProjectOffPose import (
    ProjectOffPose,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureKinds import RefPlaneFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# the portable datum keeps the selected principal plane and signed native length
def ProjectOffRef(
    DocumentValue: CadDocument,
    Datum: FeatureStep,
    Display: Parameter,
    Distance: Parameter,
) -> tuple[FeatureStep, SupportPlane, SupportPlane]:
    Definition = Datum.definition
    if type(Definition) is not RefPlaneFeature:
        raise ValueError("SOLIDWORKS offset readback lacks a typed plane definition")
    (BasePlane,) = (
        Plane
        for Plane in DocumentValue.support_planes
        if Plane.id == Definition.reference_plane_id
    )
    (Carrier,) = (
        Plane
        for Plane in DocumentValue.support_planes
        if Plane.id == Definition.support_plane_id
    )
    (OwnerId,) = Datum.input_feature_ids
    (Owner,) = (
        StepValue
        for StepValue in DocumentValue.feature_timeline
        if StepValue.id == OwnerId
    )
    NativeId = BasePlane.attributes.get("native_object_id")
    Offset = Definition.offset
    Amount = RequireScalar(Offset.value)
    if (
        Offset.unit != "mm"
        or Offset.kind != ValueKind.KLength
        or abs(Amount) != Display.value.value
        or BasePlane.attributes.get("principal") is not True
        or type(NativeId) is not int
        or Owner.kind != FeatureKind.KReference
        or Owner.attributes.get("native_object_id") != NativeId
        or Carrier.offset_parameter_id != Display.id
    ):
        raise ValueError("SOLIDWORKS offset readback datum and positive D1 disagree")
    Direction = -1 if Amount < 0 else 1
    SignedValue = Direction * RequireScalar(Distance.value.value)
    return (
        ReplaceValue(
            Datum,
            order=0,
            input_feature_ids=(),
            definition=ReplaceValue(
                Definition, offset=ReplaceValue(Distance.value, value=SignedValue)
            ),
            provenance=None,
            attributes=FreezeMapping(),
        ),
        ReplaceValue(BasePlane, provenance=None, attributes=FreezeMapping()),
        ProjectOffPose(BasePlane, Carrier, SignedValue),
    )
