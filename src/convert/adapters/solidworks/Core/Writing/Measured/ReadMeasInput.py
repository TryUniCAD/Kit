from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from interchange.Core.Common import FreezeMapping


# the explicit epoch reconstructs existing measured bytes while the report stays outside construction
def ReadMeasInput(
    OptionsValue: WriteOptions | None,
) -> tuple[int, dict[str, object], WriteOptions]:
    Settings = WriteOptions() if OptionsValue is None else OptionsValue
    if not isinstance(CastValue(object, Settings), WriteOptions):
        raise TypeError("native measurement requires ordinary write options")
    Values = dict(Settings.values)
    Source = Values.pop(KPartMeasureOpt, None)
    if Source is None:
        raise ValueError(
            "SOLIDWORKS publication requires an offline native measurement receipt"
        )
    Envelope = ReadMeasMap(Source)
    TimeValue = Envelope.get("written_at")
    if (
        set(Envelope) != {"written_at", "receipt"}
        or type(TimeValue) is not int
        or not 0 < TimeValue <= 0xFFFFFFFF
    ):
        raise ValueError(
            "native measurement requires its exact archive creation epoch and receipt"
        )
    return (
        TimeValue,
        ReadMeasMap(Envelope["receipt"]),
        ReplaceValue(Settings, values=FreezeMapping(Values)),
    )
