from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Core.Native import EncodeNativeXml


# the property package declares a standalone utf eight dom and closes empty elements explicitly
def WritePropXml(RootValue: Element) -> bytes:
    XmlBytes = EncodeNativeXml(RootValue, ShortEmptyElements=False)
    return (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
        + XmlBytes
        + b"\r\n"
    )
