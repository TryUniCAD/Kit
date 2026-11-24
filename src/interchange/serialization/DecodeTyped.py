from __future__ import annotations

from dataclasses import is_dataclass as IsDataClass
from typing import cast as CastValue

from interchange.serialization.RecordType import DataRecord
from interchange.serialization.TypeRegistry import KTypeRegistry
from interchange.serialization.WireData import KWireData


# type resolution must finish before recursion so nested assemblies retain their supported depth
def DecodeTyped(DataValue: dict[str, KWireData]) -> type[DataRecord]:
    WireType = DataValue["$type"]
    if not isinstance(WireType, str) or not WireType:
        raise ValueError("encoded record type must be nonempty text")
    TargetType = KTypeRegistry.get(WireType)
    if TargetType is None or not IsDataClass(TargetType):
        raise ValueError(f"unknown data type {WireType!r}")
    return CastValue(type[DataRecord], TargetType)
