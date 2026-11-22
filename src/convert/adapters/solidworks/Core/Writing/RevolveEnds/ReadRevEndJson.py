from hashlib import sha256 as CalcSha
from json import loads as LoadJson

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap


# only exact frozen oracle evidence is parsed as publication authority
def ReadRevEndJson(
    TextValue: object, SchemaValue: str, Digests: tuple[str, ...]
) -> dict[str, object]:
    if (
        type(TextValue) is not str
        or len(TextValue) > 600_000
        or CalcSha(TextValue.encode("utf-8")).hexdigest() not in Digests
    ):
        raise ValueError("measured revolve ends require authenticated offline evidence")
    ReportValue = ReadMeasMap(LoadJson(TextValue))
    if ReportValue.get("schema") != SchemaValue:
        raise ValueError("measured revolve end evidence has the wrong schema")
    return ReportValue
