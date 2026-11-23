from __future__ import annotations

import base64 as BaseCodec
from typing import Callable as CallableType

from interchange.serialization.WireData import KWireData

# json has no bytes tuples or sets so these single key markers carry them on the wire
KTagNames = frozenset({"$bytes", "$tuple", "$frozenset", "$set"})


# tagged containers restore python value types that plain json objects cannot express
def DecodeTagged(
    DataValue: dict[str, KWireData],
    DecoderFunc: CallableType[[KWireData], object],
) -> object:
    TagName = next(iter(DataValue))
    if TagName == "$bytes":
        EncodedValue = DataValue["$bytes"]
        if not isinstance(EncodedValue, str):
            raise ValueError("encoded bytes must be text")
        return BaseCodec.b64decode(EncodedValue, validate=True)
    ItemValues = DataValue[TagName]
    if not isinstance(ItemValues, list):
        raise ValueError(f"{TagName} value must be a list")
    DecodedValues = [DecoderFunc(ItemValue) for ItemValue in ItemValues]
    if TagName == "$tuple":
        return tuple(DecodedValues)
    if TagName == "$frozenset":
        return frozenset(DecodedValues)
    return set(DecodedValues)
