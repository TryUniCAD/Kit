from xml.etree.ElementTree import Element as XmlElement, tostring as EmitXml

from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import KMaxXmlBytes


def EmitPackageXml(Value: XmlElement) -> bytes:
    Payload: bytes = EmitXml(Value, encoding="utf-8", xml_declaration=True)
    if len(Payload) > KMaxXmlBytes:
        raise ValueError("Material XML exceeds size limit")
    return Payload
