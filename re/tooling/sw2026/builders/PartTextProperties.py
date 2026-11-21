from __future__ import annotations

from collections.abc import Mapping
from re import fullmatch
from xml.etree.ElementTree import Element, SubElement, tostring

from convert.adapters.solidworks.Drawing.Metadata.Writing.PropertyVocabulary import (
    KPropertyValueNamespace, KUserPropertyFormat,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.XmlTextValue import XmlTextValue


CUSTOM_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
CONFIG_NAMESPACE = "http://www.solidworks.com/config-properties"
SUMMARY_FORMAT = "{D5CDD502-2E9C-101B-9397-08002B2CF9AE}"
CORE_NAMESPACES = {
    "xmlns:cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "xmlns:dc": "http://purl.org/dc/elements/1.1/",
    "xmlns:dcterms": "http://purl.org/dc/terms/",
    "xmlns:dcmitype": "http://purl.org/dc/dcmitype/",
    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
SUMMARY_KEYS = {"title": "title", "subject": "subject", "author": "creator",
                "keywords": "keywords", "comments": "description"}


def simple_text(value):
    text = XmlTextValue(value, False)
    if "\r" in text or "\n" in text or "\t" in text:
        raise ValueError("ordinary part properties require single-line text")
    return text


def custom_rows(values):
    if not isinstance(values, Mapping) or len(values) > 4096:
        raise ValueError("ordinary part properties require a bounded named mapping")
    keys = set()
    rows = []
    for name, raw in values.items():
        if not isinstance(name, str) or not fullmatch(r"[A-Za-z][A-Za-z0-9 _.-]{0,127}", name):
            raise ValueError("custom property name lies outside the ordinary text profile")
        if name.casefold() in keys:
            raise ValueError("custom property names must be distinct within their scope")
        keys.add(name.casefold())
        value = simple_text(raw)
        if value.startswith(("=", "$PRP", "$PRPSHEET", "$PRPMODEL")):
            raise ValueError("ordinary text properties exclude evaluated expressions and links")
        rows.append((name, value))
    return rows


def wire(root):
    body = tostring(root, encoding="utf-8", short_empty_elements=False)
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n' + body + b"\r\n"


def core_properties(values):
    if not isinstance(values, Mapping) or set(values) - SUMMARY_KEYS.keys():
        raise ValueError("unknown file summary property")
    root = Element("cp:coreProperties", CORE_NAMESPACES)
    for name, tag in SUMMARY_KEYS.items():
        if name in values:
            SubElement(root, "dc:" + tag).text = simple_text(values[name])
    return wire(root)


def section(root, name, fmtid):
    return SubElement(root, "propertySection", {"xmlns": "", "name": name, "fmtid": fmtid})


def reserved(section_node, pid, variant, text):
    row = SubElement(section_node, "property", name="", pid=str(pid), TypeID="0")
    SubElement(row, "vt:" + variant).text = text


def dictionary(section_node, key, pid):
    SubElement(section_node, "propertyNameDictionaryElement", name=key, pid=str(pid))


def custom_properties(rows, configured):
    namespace, name = (CONFIG_NAMESPACE, "ConfigProperties") if configured else (CUSTOM_NAMESPACE, "Properties")
    root = Element(name, {"xmlns": namespace, "xmlns:vt": KPropertyValueNamespace})
    document = section(root, "DocumentSummaryInformation", SUMMARY_FORMAT)
    if not configured:
        reserved(document, 1, "i2", "65001")
        reserved(document, 22, "bool", "No")
    dictionary(document, "", 0)
    user = section(root, "UserDefinedProperties", KUserPropertyFormat)
    reserved(user, 1, "i2", "65001")
    names = {}
    for pid, (key, value) in enumerate(rows, 3):
        current = SubElement(user, "property", name=key, pid=str(pid), IsEquation="False", TypeID="0")
        SubElement(current, "vt:lpstr").text = value
        if not configured:
            SubElement(SubElement(current, "FPVals"), "vt:lpstr").text = value
        names[key] = pid
    dictionary(user, "", 0)
    for key in sorted(names):
        dictionary(user, key, names[key])
    return wire(root)


def make_property_streams(summary, document, configured):
    properties = custom_rows(document)
    settings = custom_rows(configured)
    if not (summary or properties or settings):
        raise ValueError("part property discovery requires observable neutral input")
    streams = {}
    if summary:
        streams["docProps/core.xml"] = core_properties(summary)
    if properties:
        streams["docProps/custom.xml"] = custom_properties(properties, False)
    if settings:
        streams["docProps/Config-0-Properties.xml"] = custom_properties(settings, True)
    return streams
