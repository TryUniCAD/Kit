from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.CheckPropText import (
    CheckPropText,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PropertyNames import (
    KPropertyValueNamespace,
)


# literal variant text cannot hide structured or differently typed values behind a familiar property name
def ReadPropVariant(ItemValue: Element, TypeValue: str) -> str:
    if ItemValue.tag != "{" + KPropertyValueNamespace + "}" + TypeValue:
        raise ValueError("part property has an unsupported variant type")
    if ItemValue.attrib or len(ItemValue):
        raise ValueError("part property variant contains unclassified structure")
    return CheckPropText(ItemValue.text or "")
