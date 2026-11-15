from __future__ import annotations

from builtins import getattr as GetAttr
from types import ModuleType


# complete archive parsing and exact reencoding expose fields lost by fresh metadata construction
def DecodeStreams(
    StreamData: dict[str, bytes], CodecModule: ModuleType, RegistryValue: object
) -> dict[str, object]:
    Records: dict[str, object] = {}
    for StreamName, BlobValue in StreamData.items():
        if StreamName == "swXmlContents/KeyWords":
            continue
        DocValue, Archive = GetAttr(CodecModule, "load_rooted")(
            BlobValue, RegistryValue, 1, 19000
        )
        assert GetAttr(Archive, "left")() == 0 and not GetAttr(DocValue, "tail")
        Roots = GetAttr(DocValue, "roots")
        assert len(Roots) == 1
        assert (
            GetAttr(CodecModule, "store_rooted")(DocValue, RegistryValue, 19000)
            == BlobValue
        )
        Records[StreamName] = Roots[0]
    return Records
