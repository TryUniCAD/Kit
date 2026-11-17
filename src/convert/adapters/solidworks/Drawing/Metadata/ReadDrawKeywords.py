from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import ParseXml
from convert.adapters.solidworks.Drawing.Metadata.SavedSheet import SavedSheet


# the basic inspection profile must have one real sheet and at most one view
def ReadSheetKeys(DataValue: bytes) -> SavedSheet:
    RootValue = ParseXml(DataValue)
    SheetValues = RootValue.findall("Sheet")
    if RootValue.tag != "Keywords" or len(SheetValues) != 1:
        raise SldprtFormat("drawing inspection requires one keyword sheet")
    Sheet = SheetValues[0]
    Views = Sheet.findall("View")
    if Sheet.get("Type") != "Sheet" or len(Views) > 1:
        raise SldprtFormat(
            "drawing inspection supports only one ordinary sheet and view"
        )
    SheetId = int(Sheet.get("id", "0"))
    NameValue = Sheet.get("Name", "")
    if (
        SheetId <= 0
        or NameValue == ""
        or GetSheetText(Sheet, "TemplateName") != "*.drt"
    ):
        raise SldprtFormat(
            "drawing inspection requires a named sheet without an external format"
        )
    ScaleRatio = (
        float(GetSheetText(Sheet, "ScaleNumerator")),
        float(GetSheetText(Sheet, "ScaleDenominator")),
    )
    ViewFields = GetKeywordView(RootValue, Views)
    return SavedSheet(SheetId, NameValue, ScaleRatio, *ViewFields)


# required sheet fields must occur once so competing metadata cannot choose placement
def GetSheetText(Sheet: Element, TagName: str) -> str:
    Fields = Sheet.findall(TagName)
    if len(Fields) != 1 or Fields[0].text is None:
        raise SldprtFormat(f"drawing keyword sheet has no unique {TagName} field")
    return Fields[0].text


# sheet and document view indexes must agree on the same named model link
def GetKeywordView(RootValue: Element, Views: list[Element]) -> tuple[str, str, str]:
    Index = RootValue.findall("View")
    if len(Index) != len(Views):
        raise SldprtFormat("drawing keyword view indexes disagree")
    if not Views:
        return "", "", ""
    Detail, Catalog = Views[0], Index[0]
    if Detail.attrib != Catalog.attrib or Detail.text != Catalog.text:
        raise SldprtFormat("drawing keyword views describe different model links")
    ViewFields = (
        Detail.get("Name", ""),
        Detail.text or "",
        Detail.get("Description", ""),
    )
    if not all(ViewFields):
        raise SldprtFormat("drawing keyword model link is incomplete")
    return ViewFields
