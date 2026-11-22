from xml.etree.ElementTree import Element, SubElement

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# xml display allocation follows the existing instance identifiers and references the actual ordered binary occurrences
def PutViewXmlMut(
    RootValue: Element,
    Configuration: Element,
    References: tuple[ArchiveNode, ...],
    DisplayName: str,
) -> None:
    ListId = int(RootValue.attrib["swObjCount"]) + 1
    FeatureIds = tuple(
        FieldInt(Reference.FieldsValue, "f08") for Reference in References
    )
    ListNode = SubElement(
        Configuration,
        "swDisplayStateList",
        {
            "id": str(ListId),
            "swCompNameList": "".join(f"{FeatureId}," for FeatureId in FeatureIds),
        },
    )
    _ = SubElement(
        ListNode,
        "swDisplayState",
        {
            "id": str(ListId + 1),
            "swDisplayStateName": DisplayName,
            "swShowState": "Yes," * len(FeatureIds),
        },
    )
    RootValue.set("swObjCount", str(ListId + 1))
