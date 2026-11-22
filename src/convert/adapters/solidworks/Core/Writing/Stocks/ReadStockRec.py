from hashlib import sha256 as CalcSha
from json import dumps as JsonDumps
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap

# the independently qualified two slot terminal remains the sole publication authority
KStockReceiptSha = "6b39921b4959e3662f886def026c55240227f8aab37d3246206bcf02ab8cbb7a"


# bounded plain receipt data must not invoke callbacks during canonical serialization
def CheckStockJson(Record: dict[str, object]) -> None:
    Pending: list[tuple[object, int]] = [(Record, 0)]
    CountValue = 0
    while Pending:
        Value, Depth = Pending.pop()
        CountValue += 1
        if CountValue > 1024 or Depth > 8:
            raise ValueError("selected stock measurement exceeds its bounded report")
        ValueType = type(Value)
        if ValueType is dict:
            Fields = ReadMeasMap(Value)
            for NameValue, ChildValue in Fields.items():
                if (
                    type(CastValue(object, NameValue)) is not str
                    or len(NameValue) > 128
                ):
                    raise ValueError("selected stock measurement requires plain keys")
                Pending.append((ChildValue, Depth + 1))
        elif ValueType is list:
            Children = CastValue(list[object], Value)
            if len(Children) > 16:
                raise ValueError(
                    "selected stock measurement has too many array entries"
                )
            Pending.extend((ChildValue, Depth + 1) for ChildValue in Children)
        elif not (
            Value is None
            or type(Value) is bool
            or type(Value) is int
            and 0 <= Value <= 0xFFFFFFFF
            or type(Value) is str
            and len(Value) <= 512
        ):
            raise ValueError("selected stock measurement requires bounded JSON data")


# hash verification preserves the exact corrected report rather than a caller substitute
def CheckStockRec(Record: dict[str, object]) -> None:
    if set(Record) != {"freeze", "native", "staged"}:
        raise ValueError(
            "selected stock output requires its exact controlled native receipt"
        )
    CheckStockJson(Record)
    Canonical = JsonDumps(Record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if CalcSha(Canonical.encode("utf-8")).hexdigest() != KStockReceiptSha:
        raise ValueError(
            "selected stock output requires its exact controlled native receipt"
        )


# the compact evaluator sections have independent freeze and stage record digests
def StockWireSha(Record: dict[str, object]) -> str:
    Payload = (
        JsonDumps(Record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")
    return CalcSha(Payload).hexdigest()
