from hashlib import sha256 as CalcSha
from json import dumps as DumpJson

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)

# the canonical semantic digest authenticates the exact disclosed native edit and fresh reopen record
KEqReceiptSha = "ad8a597ed8c2144d8369829dbfd6395484afd914c4b01fa194758faddd19f666"


# native equation certification requires the complete measured report beside the exact event time
def ReadEqMeas(
    OptionsValue: WriteOptions,
) -> tuple[int, dict[str, object], WriteOptions]:
    TimeValue, Receipt, SettingsValue = ReadMeasInput(OptionsValue)
    ReceiptBytes = DumpJson(
        Receipt, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    if CalcSha(ReceiptBytes).hexdigest() != KEqReceiptSha:
        raise ValueError(
            "native measurement requires the authenticated width-depth report"
        )
    return TimeValue, Receipt, SettingsValue
