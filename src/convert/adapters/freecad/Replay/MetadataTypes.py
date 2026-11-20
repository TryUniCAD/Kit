from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeGuard


# mapping payload checks need a shared guard so archive readers narrow safely
def IsPayloadMap(Value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(Value, Mapping)


# sequence payloads require a concrete element contract before archive fields are traversed
def IsPayloadSeq(Value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(Value, Sequence) and not isinstance(
        Value, (str, bytes, bytearray)
    )
