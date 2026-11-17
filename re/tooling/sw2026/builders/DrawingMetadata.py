from __future__ import annotations

from dataclasses import dataclass
from pathlib import PureWindowsPath
from xml.etree.ElementTree import Element, SubElement, tostring

from Core import Obj
from builders.DrawingSheet import DrawingSheet, _paper_text
from builders.Metadata import integer
from builders.PropertySections import text_information_properties
from convert.adapters.solidworks.Container.Format import KEYWORDS_STREAM, KPartSuffix


INFORMATION_STREAM = "docProps/ISolidWorksInformation.xml"
_XML_HEADER = b'<?xml version="1.0" encoding="UTF-8"?>\r\n'


def _xml(element):
    return _XML_HEADER + tostring(element, encoding="utf-8", short_empty_elements=True).replace(b" />", b"/>") + b"\r\n"


def _fixed(value):
    return format(value, ".6f")


@dataclass(frozen=True, slots=True)
class DrawingViewIndex:
    name: str
    path: PureWindowsPath
    configuration: str
    configuration_id: int

    @classmethod
    def from_view(cls, view):
        if not isinstance(view, Obj) or view.cls != "moAbsoluteView":
            raise ValueError("drawing view indexes require a generated absolute view")
        reference = view["f5d8"]
        file = reference["f3b0"]["shared"]
        config = reference["f3c0"]
        path = PureWindowsPath(_paper_text(file["h18"]["f08"], "drawing model path"))
        if file["f20"] != 2 or not path.is_absolute() or path.suffix.casefold() != KPartSuffix:
            raise ValueError("drawing indexes require an absolute native part path")
        if path.stem.casefold() != file["h10"]["f08"].casefold():
            raise ValueError("drawing part filename and directory model name differ")
        return cls(
            _paper_text(view["f18"]["f08"], "drawing view name"), path,
            _paper_text(config["f08"], "drawing configuration name"),
            integer(config["f10"], "drawing configuration id", high=0x7FFFFFFE),
        )

    def add_keyword(self, owner):
        SubElement(owner, "View", id=str(self.configuration_id), Name=self.name,
                   Description=self.configuration).text = self.path.stem + KPartSuffix

    def layout_value(self, sheet):
        return "@".join(("1:", "", self.configuration, str(self.configuration_id), str(self.path), self.name, sheet.name))


def drawing_keywords(*, document_name, created_at, sheet, sheet_id, model_view=None):
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
    if model_view is not None:
        model_view.add_keyword(record)
        model_view.add_keyword(root)
    SubElement(record, "id", id="").text = item_id
    return b"\x86" + _xml(root)


def drawing_layout_properties(*, sheet, model_view=None):
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
        "SW-Config-Model-View-Sheet-List": "0:" if model_view is None else model_view.layout_value(sheet),
        "SW-All Sheet Format Data": expanded,
    }


def drawing_sheet_indexes(*, document_name, created_at, sheet, sheet_id, model_view=None):
    properties = drawing_layout_properties(sheet=sheet, model_view=model_view)
    root = text_information_properties(properties)
    return {
        KEYWORDS_STREAM: drawing_keywords(document_name=document_name, created_at=created_at, sheet=sheet, sheet_id=sheet_id, model_view=model_view),
        INFORMATION_STREAM: _xml(root),
    }
