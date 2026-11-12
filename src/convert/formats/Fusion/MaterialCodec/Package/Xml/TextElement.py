from collections.abc import Mapping
from xml.etree.ElementTree import Element as XmlElement, TreeBuilder


def TextElement(
    TagName: str, Attributes: Mapping[str, str], TextValue: str
) -> XmlElement:
    Builder = TreeBuilder()
    _ = Builder.start(TagName, dict(Attributes))
    Builder.data(TextValue)
    _ = Builder.end(TagName)
    return Builder.close()
