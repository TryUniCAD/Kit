from xml.etree.ElementTree import Element, tostring as WriteXml


# the property package declares a standalone utf eight dom and closes empty elements explicitly
def WritePropXml(RootValue: Element) -> bytes:
    XmlBytes: bytes = WriteXml(RootValue, encoding="utf-8", short_empty_elements=False)
    return (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
        + XmlBytes
        + b"\r\n"
    )
