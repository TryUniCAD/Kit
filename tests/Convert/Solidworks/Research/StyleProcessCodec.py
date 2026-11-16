from __future__ import annotations

from builtins import getattr as GetAttr
from types import ModuleType
from typing import cast as CastValue


# full archive decoding and byte identity expose field omissions in freshly constructed records
def RoundTrip(
    Record: object, CodecModule: ModuleType, RegistryValue: object
) -> tuple[object, bytes]:
    DocValue = GetAttr(CodecModule, "StreamDoc")("rooted", {"base": 1}, [Record])
    BlobValue = CastValue(
        bytes, GetAttr(CodecModule, "store_rooted")(DocValue, RegistryValue, 19000)
    )
    Decoded, Archive = GetAttr(CodecModule, "load_rooted")(
        BlobValue, RegistryValue, 1, 19000
    )
    assert GetAttr(Archive, "left")() == 0 and not GetAttr(Decoded, "tail")
    DecodedRoots = CastValue(list[object], GetAttr(Decoded, "roots"))
    assert len(DecodedRoots) == 1
    assert (
        GetAttr(CodecModule, "store_rooted")(Decoded, RegistryValue, 19000) == BlobValue
    )
    return DecodedRoots[0], BlobValue
