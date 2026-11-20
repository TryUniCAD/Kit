from typing import cast as CastValue
from xml.etree.ElementTree import Element

# name tokens must remain within their own markup after serialization
KNameDelimiters = frozenset(" \t\r\n<>&\"'=/!?")


# name syntax belongs to the xml parser while token boundaries protect authored names
def CheckXmlNames(RootValue: Element) -> None:
    for NodeValue in RootValue.iter():
        TagValue = CastValue(object, NodeValue.tag)
        if TagValue is None or callable(TagValue):
            raise ValueError("native keyword framing requires named elements")
        for AuthoredName in (TagValue, *NodeValue.attrib):
            NameValue = str(AuthoredName)
            if NameValue.startswith("{"):
                NameValue = NameValue.rpartition("}")[2]
            if not NameValue or not KNameDelimiters.isdisjoint(NameValue):
                raise ValueError(
                    "native keyword framing requires well-formed XML names"
                )
