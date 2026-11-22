from hashlib import sha256 as CalcSha
from json import loads as LoadJson
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap


# exact receipt bytes must match a trusted unconditional pin before parsing
def ReadBoxRecord(RawValue: object, Expected: str, NameValue: str) -> dict[str, object]:
    if type(RawValue) is not str or not 0 < len(RawValue) <= 512 * 1024:
        raise ValueError(
            f"attached box measurement requires its exact {NameValue} record"
        )
    if CalcSha(RawValue.encode("utf-8")).hexdigest() != Expected:
        raise ValueError(f"attached box measurement {NameValue} digest differs")
    return ReadMeasMap(CastValue(object, LoadJson(RawValue)))
