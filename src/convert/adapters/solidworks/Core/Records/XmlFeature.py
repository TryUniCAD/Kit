from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.NativeDimension import NativeDimension


# keyword features need shared dimensions before native stream ownership is resolved
@Dataclass(slots=True)
class XmlFeature:
    object_id: int
    name: str
    kind: str
    xml_tag: str
    properties: dict[str, str]
    dimensions: list[NativeDimension]
