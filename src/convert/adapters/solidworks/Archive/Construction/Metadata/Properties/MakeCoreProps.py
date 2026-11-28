from collections.abc import Mapping
from xml.etree.ElementTree import Element, SubElement

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.CheckPropText import (
    CheckPropText,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PropertyNames import (
    KSummaryNamespaces,
    KSummaryTags,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.WritePropXml import (
    WritePropXml,
)


# fresh file summary text belongs to the exact native core vocabulary while save times remain native state
def MakeCoreProps(SummaryFields: Mapping[str, object]) -> bytes:
    if set(SummaryFields) - KSummaryTags.keys():
        raise ValueError("part summary contains an unsupported field")
    RootValue = Element("cp:coreProperties", KSummaryNamespaces)
    for FieldName, ElementName in KSummaryTags.items():
        if FieldName in SummaryFields:
            setattr(
                SubElement(RootValue, "dc:" + ElementName),
                "text",
                CheckPropText(SummaryFields[FieldName]),
            )
    return WritePropXml(RootValue)
