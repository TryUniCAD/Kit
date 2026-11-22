from hashlib import sha256 as CalcSha
from json import loads as LoadJson

from convert.adapters.solidworks.Core.Writing.Circle.CircAuthPins import KCircAuthPins
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap


# validate the whole terminal report text before interpreting any result row
def ReadCircAuth(
    Receipt: dict[str, object],
) -> tuple[str, str, dict[str, object]]:
    TextValue = Receipt.get("native_report")
    if (
        set(Receipt) != {"native_report"}
        or type(TextValue) is not str
        or len(TextValue) > 200_000
    ):
        raise ValueError("circle publication requires bounded exact native report text")
    RawValue = TextValue.encode("utf-8")
    ReportSha = CalcSha(RawValue).hexdigest()
    PinsValue = KCircAuthPins.get(ReportSha)
    if PinsValue is None:
        raise ValueError("circle publication requires authenticated offline evidence")
    Schema, Passed = PinsValue
    Report = ReadMeasMap(LoadJson(RawValue))
    if Report.get("schema") != Schema or Report.get(Passed) is not True:
        raise ValueError("circle publication requires a passing exact native report")
    return Schema, ReportSha, Report
