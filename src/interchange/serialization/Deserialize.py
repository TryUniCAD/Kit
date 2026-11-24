from __future__ import annotations

from interchange.serialization.DecodeValue import DecodeValue


# separate decode operations must not reuse metadata changed by compatibility binding
def FromData(SourceValue: object) -> object:
    return DecodeValue(SourceValue, {})
