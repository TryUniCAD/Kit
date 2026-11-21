from xml.etree.ElementTree import Element, SubElement

from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import (
    FrameKeywords,
)
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Drawing.Construction.Indexes.DrawViewIndex import (
    DrawViewIndex,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.DrawSheetIndex import (
    DrawSheetIndex,
)


# linked keywords publish the same selected model view beneath the sheet and document while retaining the native sheet child order
def MakeViewKeys(
    NameValue: str, CreatedAt: int, SheetValue: DrawSheetIndex, ViewValue: DrawViewIndex
) -> bytes:
    RootValue = Element("Keywords", {"id": str(CreatedAt), "Name": NameValue})
    Identifier = str(SheetValue.IdValue)
    Record = SubElement(
        RootValue, "Sheet", id=Identifier, Name=SheetValue.NameValue, Type="Sheet"
    )
    ValuesValue = (
        ("CustomPropertyView", {"id": "", "Name": ""}, SheetValue.PropertyView),
        ("PaperSize", {"id": "", "Description": "0"}, "A_H"),
        ("ScaleDenominator", {"id": ""}, format(SheetValue.Denominator, ".6f")),
        ("ScaleNumerator", {"id": ""}, format(SheetValue.Numerator, ".6f")),
        ("TemplateName", {"id": ""}, "*.drt"),
    )
    for TagValue, Attributes, TextValue in ValuesValue:
        setattr(SubElement(Record, TagValue, Attributes), "text", TextValue)
    for Parent in (Record, RootValue):
        setattr(
            SubElement(
                Parent,
                "View",
                id=str(ViewValue.ConfigId),
                Name=ViewValue.NameValue,
                Description=ViewValue.ConfigName,
            ),
            "text",
            ViewValue.PathValue.stem + KPartSuffix,
        )
    setattr(SubElement(Record, "id", {"id": ""}), "text", Identifier)
    return FrameKeywords(RootValue, True)
