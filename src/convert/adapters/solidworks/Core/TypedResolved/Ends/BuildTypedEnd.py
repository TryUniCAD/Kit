from convert.adapters.solidworks.Core.Native import NativeOperation
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Records.RecordParameter import ParameterValue


# verified native end owners must reach the neutral feature without losing reversal symmetry or a second blind length
def BuildTypedEnd(
    Operation: NativeOperation, EndValue: ExtrudeEnd, DepthValue: float | None
) -> ExtrudeFeature:
    SecondValue = Operation.second_length_mm
    return ExtrudeFeature(
        (
            None
            if DepthValue is None
            else ParameterValue(DepthValue, ValueKind.KLength, "mm")
        ),
        end_condition=EndValue,
        reversed=Operation.direction_code == 1,
        symmetric=EndValue == ExtrudeEnd.KMidPlane,
        second_length=(
            None
            if SecondValue is None
            else ParameterValue(SecondValue, ValueKind.KLength, "mm")
        ),
        second_end_condition=(
            ExtrudeEnd.KBlind
            if SecondValue is not None
            else Operation.second_extrusion_end
        ),
    )
