from hashlib import sha256 as CalcSha
from json import loads as LoadJson

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart


# confirm exact unicode evidence bytes before interpreting any report fields
def ReadAuthRevJson(TextValue: object, Digest: str, Schema: str) -> dict[str, object]:
    if type(TextValue) is not str or len(TextValue) > 600_000:
        raise ValueError("measured revolve requires bounded exact evidence text")
    Payload = TextValue.encode("utf-8")
    if CalcSha(Payload).hexdigest() != Digest:
        raise ValueError("measured revolve requires authenticated offline evidence")
    Result = ReadMeasMap(LoadJson(Payload))
    if (
        Result.get("schema") != Schema
        or Result.get("oracle_sha256") != KOraclePart["sha256"]
    ):
        raise ValueError("measured revolve evidence has the wrong schema or oracle")
    return Result
