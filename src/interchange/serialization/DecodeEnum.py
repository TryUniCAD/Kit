from __future__ import annotations

from enum import Enum as EnumBase
from typing import Callable as CallableType

from interchange.serialization.TypeRegistry import KTypeRegistry
from interchange.serialization.WireData import KWireData


# enum members travel by registered type name so only known enum classes may be rebuilt
def DecodeEnum(
    DataValue: dict[str, KWireData],
    DecoderFunc: CallableType[[KWireData], object],
) -> object:
    if set(DataValue) != {"$enum", "value"}:
        raise ValueError("encoded enum must contain only type and value")
    EnumName = DataValue["$enum"]
    if not isinstance(EnumName, str) or not EnumName:
        raise ValueError("encoded enum type must be nonempty text")
    EnumType = KTypeRegistry.get(EnumName)
    if EnumType is None or not issubclass(EnumType, EnumBase):
        raise ValueError(f"unknown enum type {EnumName!r}")
    return EnumType(DecoderFunc(DataValue["value"]))
