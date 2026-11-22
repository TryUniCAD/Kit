from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Records.RecordParameter import ParameterValue


# the physical driver word must recover the authored millimetre value in the typed read path
def ReadRectLength(ValueInput: ParameterValue | None) -> float:
    MetresValue = ReadLength(ValueInput)
    if (
        ValueInput is not None
        and ValueInput.unit == "mm"
        and MetresValue / 0.001 != RequireScalar(ValueInput.value)
    ):
        raise ValueError(
            "native rectangle cannot preserve the authored millimetre driver"
        )
    return MetresValue
