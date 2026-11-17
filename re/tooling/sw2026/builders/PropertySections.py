from __future__ import annotations

from collections.abc import Mapping
from xml.etree.ElementTree import Element, SubElement


INFORMATION_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/SolidworksInformation-properties"
VALUE_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
USER_DEFINED_FORMAT_ID = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"
USER_DEFINED_SECTION_NAME = "UserDefinedProperties"


def text_information_properties(properties):
    if not isinstance(properties, Mapping):
        raise TypeError("text information properties require an ordered mapping")
    root = Element("{" + INFORMATION_NAMESPACE + "}Properties", {"xmlns:vt": VALUE_NAMESPACE})
    section = SubElement(root, "propertySection", name=USER_DEFINED_SECTION_NAME, fmtid=USER_DEFINED_FORMAT_ID)
    rows = tuple(properties.items())
    if len(rows) + 2 >= 0x1000000:
        raise ValueError("text information properties exceed the ordinary property id domain")
    for pid, (name, value) in enumerate(rows, 3):
        if not isinstance(name, str) or not name or not isinstance(value, str):
            raise ValueError("ordinary text properties require nonempty names and string values")
        item = SubElement(section, "property", name=name, pid=str(pid))
        SubElement(item, "vt:lpstr").text = value
    for pid, (name, _) in enumerate(rows, 3):
        SubElement(section, "propertyNameDictionaryElement", name=name, pid=str(pid))
    return root
