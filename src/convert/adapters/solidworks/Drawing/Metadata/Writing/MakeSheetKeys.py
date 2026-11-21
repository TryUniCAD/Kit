from xml.etree.ElementTree import Element, SubElement

from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import (
    FrameKeywords,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckDrawText import (
    CheckDrawText,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.DrawSheetIndex import (
    DrawSheetIndex,
)


# blank drawing keyword fields must derive from the actual sheet and use the native paper vocabulary and stream framing
def MakeSheetKeys(NameValue: str, CreatedAt: int, SheetValue: DrawSheetIndex) -> bytes:
    CheckDrawText(NameValue, True)
    if (
        type(CreatedAt) is not int
        or not 0 <= CreatedAt <= 4294967295
        or type(SheetValue) is not DrawSheetIndex
    ):
        raise ValueError(
            "drawing keyword construction requires actual sheet identity and explicit creation time"
        )
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
        ("id", {"id": ""}, Identifier),
    )
    for TagValue, Attributes, TextValue in ValuesValue:
        setattr(SubElement(Record, TagValue, Attributes), "text", TextValue)
    return FrameKeywords(RootValue, True)
