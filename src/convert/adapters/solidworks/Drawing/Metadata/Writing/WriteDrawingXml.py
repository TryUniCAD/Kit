from xml.etree.ElementTree import Element, tostring as XmlBytes


# drawing package xml requires the native declaration line endings and empty element spelling without saved payloads
def WriteDrawingXml(RootValue: Element) -> bytes:
    RawValue: bytes = XmlBytes(RootValue, encoding="utf-8", short_empty_elements=True)
    PayloadValue = RawValue.replace(b" />", b"/>")
    return b'<?xml version="1.0" encoding="UTF-8"?>\r\n' + PayloadValue + b"\r\n"
