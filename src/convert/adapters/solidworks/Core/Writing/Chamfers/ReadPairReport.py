from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap


# canonical measurement metadata must hash to the exact authority observed by the runner
def ReadPairReport(Value: object) -> tuple[dict[str, object], str]:
    TextValue = (
        DumpJson(ReadMeasMap(Value), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return (
        ReadMeasMap(LoadJson(TextValue)),
        CalcSha(TextValue.encode("utf-8")).hexdigest(),
    )
