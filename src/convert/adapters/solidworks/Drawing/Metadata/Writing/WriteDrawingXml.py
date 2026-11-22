from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Core.Native import EncodeNativeXml


# drawing package xml requires the native declaration line endings and empty element spelling without saved payloads
def WriteDrawingXml(RootValue: Element) -> bytes:
    RawValue = EncodeNativeXml(RootValue)
    PayloadValue = RawValue.replace(b" />", b"/>")
    return b'<?xml version="1.0" encoding="UTF-8"?>\r\n' + PayloadValue + b"\r\n"
