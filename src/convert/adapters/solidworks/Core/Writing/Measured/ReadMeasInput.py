from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap


# the reported authoring time reconstructs already measured bytes without deriving intent from the receipt
def ReadMeasInput(OptionsValue: WriteOptions) -> tuple[int, dict[str, object]]:
    SourceValue = OptionsValue.values.get(KPartMeasureOpt)
    if SourceValue is None:
        raise ValueError(
            "SOLIDWORKS part publication requires an offline native measurement receipt"
        )
    Envelope = ReadMeasMap(SourceValue)
    TimeValue = Envelope.get("written_at")
    if (
        set(Envelope) != {"written_at", "receipt"}
        or type(TimeValue) is not int
        or not 0 <= TimeValue <= 0xFFFFFFFF
    ):
        raise ValueError(
            "native measurement requires its exact archive creation epoch and receipt"
        )
    return TimeValue, ReadMeasMap(Envelope["receipt"])
