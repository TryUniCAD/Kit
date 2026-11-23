from __future__ import annotations

from dataclasses import is_dataclass as IsDataClass
from typing import Callable as CallableType
from typing import cast as CastValue

from interchange.serialization.DecodeRecord import DecodeRecord
from interchange.serialization.RecordType import DataRecord
from interchange.serialization.TypeRegistry import KTypeRegistry
from interchange.serialization.WireData import KWireData


# model records travel by registered type name so only known dataclasses may be constructed
def DecodeTyped(
    DataValue: dict[str, KWireData],
    DecoderFunc: CallableType[[KWireData], object],
) -> object:
    WireType = DataValue["$type"]
    if not isinstance(WireType, str) or not WireType:
        raise ValueError("encoded record type must be nonempty text")
    TargetType = KTypeRegistry.get(WireType)
    if TargetType is None or not IsDataClass(TargetType):
        raise ValueError(f"unknown data type {WireType!r}")
    RecordType = CastValue(type[DataRecord], TargetType)
    return DecodeRecord(DataValue, RecordType, DecoderFunc)
