from collections.abc import Mapping
from math import pi as PiValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatPick import (
    CheckPatPick,
)
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.BoundPlaneValues import ReadPlaneParam
from interchange.Features.FeatureBoundPlane import BoundDatum
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# the angled support must be owned by its live scalar hinge and right plane
def ReadPatAngle(
    StepValue: FeatureStep,
    HingeId: str,
    AnglePlane: SupportPlane,
    RightPlane: SupportPlane,
    PickValues: Mapping[str, Selection],
    ParamValues: Mapping[str, Parameter],
) -> tuple[str, float]:
    Definition = StepValue.definition
    if type(Definition) is not BoundDatum or Definition.Method != "angle":
        raise ValueError(
            "angled datum requires its actual bound angle and evaluated support"
        )
    if (
        StepValue.kind is not FeatureKind.KReference
        or StepValue.input_feature_ids != (HingeId,)
        or StepValue.sketch_id is not None
        or StepValue.operation is not None
        or len(StepValue.selection_ids) != 2
        or Definition.ReferenceFrame != RightPlane.transform
    ):
        raise ValueError(
            "angled datum must depend on its preceding finite hinge and actual Right support"
        )
    FaceId, AxisId = StepValue.selection_ids
    CheckPatPick(PickValues[FaceId], "support_plane", RightPlane.id)
    CheckPatPick(PickValues[AxisId], "feature", HingeId)
    if (
        AnglePlane.id != Definition.SupportPlaneId
        or AnglePlane.name != StepValue.name
        or AnglePlane.support_selection_id != FaceId
        or AnglePlane.offset_parameter_id != Definition.OffsetParameterId
        or StepValue.parameter_ids
        != (Definition.ScalarParameterId, Definition.OffsetParameterId)
    ):
        raise ValueError(
            "angled datum output and scalar roles must join its actual evaluated support"
        )
    AngleParam = ParamValues[Definition.ScalarParameterId]
    OffsetParam = ParamValues[Definition.OffsetParameterId]
    CheckCircDrive(AngleParam, StepValue.id, "D1")
    if (
        OffsetParam.owner_id != StepValue.id
        or OffsetParam.name != "Reference offset"
        or OffsetParam.role is not ParameterRole.KDerived
        or OffsetParam.expression is not None
        or ReadPlaneParam(StepValue, OffsetParam.id, ParamValues, ValueKind.KLength)
        != 0.0
    ):
        raise ValueError("inactive datum offset is only a derived zero invariant")
    RadiansValue = ReadPlaneParam(
        StepValue, AngleParam.id, ParamValues, ValueKind.KAngle
    )
    if not 0.0 < RadiansValue < PiValue / 2.0:
        raise ValueError(
            "only the acute positive Right plane angle profile is admitted"
        )
    return AngleParam.id, RadiansValue
