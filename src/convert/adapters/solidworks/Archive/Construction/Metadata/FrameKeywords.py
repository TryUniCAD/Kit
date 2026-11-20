from typing import cast as CastValue
from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Core.Native import SerializeKeywordXml


# part and drawing keyword owners share verified native utf eight framing while preserving their distinct empty element formatting
def FrameKeywords(RootValue: Element, CompactTags: bool) -> bytes:
    if type(CastValue(object, CompactTags)) is not bool or RootValue.tag != "Keywords":
        raise ValueError(
            "native keyword framing requires the actual keyword root and explicit formatting mode"
        )
    if RootValue.tail:
        raise ValueError(
            "native keyword framing requires content inside the keyword root"
        )
    PayloadValue = SerializeKeywordXml(RootValue).replace(b"\r", b"&#13;")
    if CompactTags:
        PayloadValue = PayloadValue.replace(b" />", b"/>")
    return b'\x86<?xml version="1.0" encoding="UTF-8"?>\r\n' + PayloadValue + b"\r\n"
