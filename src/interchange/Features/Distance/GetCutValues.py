from typing import Mapping as TypeMap

from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.Distance.DistanceCut import DistanceCut
from interchange.Features.DistanceParam import GetDistParam
from interchange.Features.DistanceSpan import GetDistSpan
from interchange.Features.DistanceValues import DistExtValues
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# cut geometry evaluates the exact owned distance without treating a modifying operation as a creation
def GetCutValues(
    StepValue: FeatureStep, Definition: DistanceCut, Parameters: TypeMap[str, Parameter]
) -> DistExtValues:
    if (
        StepValue.kind != FeatureKind.KExtrusion
        or StepValue.operation != BooleanOp.KCutOperation
    ):
        raise ValueError("distance cut requires a modifying extrusion feature")
    Extent = Definition.Extrusion
    if Extent.SideMode != "one_sided" or any(
        Identity is not None
        for Identity in (
            Extent.AgainstParameterId,
            Extent.StartOffsetId,
            Extent.SecondTaperId,
        )
    ):
        raise ValueError(
            "distance cut currently requires a single profile relative extent"
        )
    Along = GetDistParam(
        StepValue, Extent.AlongParameterId, Parameters, ValueKind.KLength
    )
    Taper = (
        0.0
        if Extent.TaperParameterId is None
        else GetDistParam(
            StepValue, Extent.TaperParameterId, Parameters, ValueKind.KAngle
        )
    )
    if Taper != 0.0:
        raise ValueError("distance cut currently requires an untapered tool")
    Lower, Upper = GetDistSpan(Along, None, 0.0, Extent.SideMode)
    return DistExtValues(Lower, Upper, 0.0, Taper, None)
