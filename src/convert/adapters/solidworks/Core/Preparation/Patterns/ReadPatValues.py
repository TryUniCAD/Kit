from collections.abc import Mapping
from math import dist as Distance
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatPick import (
    CheckPatPick,
)
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureKinds import LinearPattern
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.PlaneExtAxis import GetExtVector
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# the two pattern controls must follow the actual local seed and signed support direction
def ReadPatValues(
    StepValue: FeatureStep,
    SeedId: str,
    AngleId: str,
    AnglePlane: SupportPlane,
    PickValues: Mapping[str, Selection],
    ParamValues: Mapping[str, Parameter],
) -> tuple[int, float, bool]:
    Definition = StepValue.definition
    if (
        type(Definition) is not LinearPattern
        or StepValue.kind is not FeatureKind.KPattern
        or StepValue.operation is not BooleanOp.KJoin
        or StepValue.sketch_id is not None
        or StepValue.input_feature_ids != (SeedId, AngleId)
        or len(StepValue.selection_ids) != 2
        or StepValue.selection_ids[0] != Definition.direction_selection_id
    ):
        raise ValueError(
            "pattern must retain actual ordered seed and plane dependencies"
        )
    DirectionId, BodyId = StepValue.selection_ids
    CheckPatPick(PickValues[DirectionId], "support_plane", AnglePlane.id)
    CheckPatPick(PickValues[BodyId], "feature", SeedId, "body")
    if len(StepValue.parameter_ids) != 2:
        raise ValueError("pattern requires actual independent count and pitch drivers")
    CountId, PitchId = StepValue.parameter_ids
    CountParam, PitchParam = ParamValues[CountId], ParamValues[PitchId]
    CheckCircDrive(CountParam, StepValue.id, "D1")
    CheckCircDrive(PitchParam, StepValue.id, "D3")
    CountValue = CountParam.value.value
    if (
        type(CastValue(object, Definition.reversed)) is not bool
        or type(Definition.instance_count) is not int
        or type(CountValue) is not int
        or CountParam.value.kind is not ValueKind.KInteger
        or CountParam.value.unit != ""
        or CountValue != Definition.instance_count
        or PitchParam.value != Definition.spacing
    ):
        raise ValueError(
            "pattern D1 and D3 drivers disagree with the actual signed count and pitch"
        )
    PitchValue = ReadLength(PitchParam.value)
    if not 2 <= CountValue <= 8:
        raise ValueError(
            "ordinary local pattern requires an active positive pitch and two to eight instances"
        )
    Normal = GetExtVector(AnglePlane.transform.z_axis)
    if Normal[2] != 0.0 or abs(Distance(Normal, (0.0, 0.0, 0.0)) - 1.0) >= 1e-14:
        raise ValueError(
            "local pattern must use the actual signed direction in the seed sketch plane"
        )
    return CountValue, PitchValue, Definition.reversed
