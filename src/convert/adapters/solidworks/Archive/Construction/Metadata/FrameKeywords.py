from typing import cast as CastValue
from xml.etree.ElementTree import Element, QName, tostring as XmlBytes


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
    if any(
        not isinstance(NodeValue.tag, (str, QName)) for NodeValue in RootValue.iter()
    ):
        raise ValueError("native keyword framing requires named elements")
    PayloadValue = CastValue(
        bytes, XmlBytes(RootValue, encoding="utf-8", short_empty_elements=True)
    )
    PayloadValue = PayloadValue.replace(b"\r", b"&#13;")
    if CompactTags:
        PayloadValue = PayloadValue.replace(b" />", b"/>")
    return b'\x86<?xml version="1.0" encoding="UTF-8"?>\r\n' + PayloadValue + b"\r\n"
