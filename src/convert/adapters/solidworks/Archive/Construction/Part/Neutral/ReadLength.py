from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import ParameterValue


# typed neutral lengths must convert through their explicit units without interpreting arbitrary numeric strings or native saved metadata
def ReadLength(ValueInput: ParameterValue) -> float:
    if type(ValueInput) is not ParameterValue or ValueInput.kind != ValueKind.KLength:
        raise ValueError("plain boss requires an explicitly typed length")
    ScalesValue = {"mm": 0.001, "m": 1.0, "in": 0.0254}
    if ValueInput.unit not in ScalesValue:
        raise ValueError(
            "plain boss length requires explicit millimetre metre or inch units"
        )
    NumberValue = RequireScalar(ValueInput.value) * ScalesValue[ValueInput.unit]
    if NumberValue < 1e-14:
        raise ValueError(
            "plain boss depth must be at least one e minus fourteen metres"
        )
    return NumberValue
