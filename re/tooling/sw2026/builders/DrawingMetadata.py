from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring

from builders.DrawingSheet import DrawingSheet, _paper_text
from builders.Metadata import integer
from convert.adapters.solidworks.Container.Format import KEYWORDS_STREAM
from convert.adapters.solidworks.Drawing.Metadata.ReadDrawProps import KDrawPropNamespace, KPropertyTextTag


INFORMATION_STREAM = "docProps/ISolidWorksInformation.xml"
_XML_HEADER = b'<?xml version="1.0" encoding="UTF-8"?>\r\n'


def _xml(element):
    return _XML_HEADER + tostring(element, encoding="utf-8", short_empty_elements=True).replace(b" />", b"/>") + b"\r\n"


def _fixed(value):
    return format(value, ".6f")


def drawing_keywords(*, document_name, created_at, sheet, sheet_id):
    if not isinstance(sheet, DrawingSheet):
        raise ValueError("drawing keywords require generated sheet settings")
    name = _paper_text(document_name, "drawing name")
    root = Element("Keywords", id=str(integer(created_at, "drawing creation time")), Name=name)
    item_id = str(integer(sheet_id, "drawing sheet id", low=1, high=0x7FFFFFFF))
    record = SubElement(root, "Sheet", id=item_id, Name=sheet.name, Type="Sheet")
    SubElement(record, "CustomPropertyView", id="", Name="").text = sheet.custom_property_view
    SubElement(record, "PaperSize", id="", Description=str(sheet.native_paper_code)).text = sheet.native_paper_name
    SubElement(record, "ScaleDenominator", id="").text = _fixed(sheet.scale_denominator)
    SubElement(record, "ScaleNumerator", id="").text = _fixed(sheet.scale_numerator)
    SubElement(record, "TemplateName", id="").text = sheet.native_template_name
    SubElement(record, "id", id="").text = item_id
    return b"\x86" + _xml(root)


def drawing_layout_properties(*, sheet):
    if not isinstance(sheet, DrawingSheet):
        raise ValueError("drawing property indexes require generated sheet settings")
    width, height = sheet.dimensions
    empty_sheet = (sheet.native_paper_code, width, height, sheet.scale_numerator, sheet.scale_denominator, 0)
    expanded = "@".join((sheet.name, *map(_fixed, empty_sheet), "", ""))
    return {
        "SW-Current Sheet": "1",
        "SW-Total Sheets": "1",
        "SW-Sheet Name": sheet.name,
        "SW-All Sheet Names": sheet.name + "@",
        "SW-Config-Model-View-Sheet-List": "0:",
        "SW-All Sheet Format Data": expanded,
    }


def drawing_sheet_indexes(*, document_name, created_at, sheet, sheet_id):
    properties = drawing_layout_properties(sheet=sheet)
    root = Element(KDrawPropNamespace + "Properties")
    values = SubElement(root, "Properties")
    for ordinal, (name, value) in enumerate(properties.items(), 2):
        record = SubElement(values, "property", name=name, pid=str(ordinal))
        SubElement(record, KPropertyTextTag).text = value
    return {
        KEYWORDS_STREAM: drawing_keywords(document_name=document_name, created_at=created_at, sheet=sheet, sheet_id=sheet_id),
        INFORMATION_STREAM: _xml(root),
    }
