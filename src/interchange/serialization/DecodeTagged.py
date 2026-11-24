from __future__ import annotations

import base64 as BaseCodec
from typing import cast as CastValue

# json has no bytes tuples or sets so these single key markers carry them on the wire
KTagNames = frozenset({"$bytes", "$tuple", "$frozenset", "$set"})


# container construction must follow child traversal without retaining another recursive helper frame
def DecodeTagged(TagName: str, DecodedValue: object) -> object:
    if TagName == "$bytes":
        if not isinstance(DecodedValue, str):
            raise ValueError("encoded bytes must be text")
        return BaseCodec.b64decode(DecodedValue, validate=True)
    if not isinstance(DecodedValue, list):
        raise ValueError(f"{TagName} value must be a list")
    DecodedValues = CastValue(list[object], DecodedValue)
    if TagName == "$tuple":
        return tuple(DecodedValues)
    if TagName == "$frozenset":
        return frozenset(DecodedValues)
    return set(DecodedValues)
