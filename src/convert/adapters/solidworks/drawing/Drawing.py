from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path as FilePath
import xml.etree.ElementTree as XmlTree  # noqa: DUO107

from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.container.Format import (
    INFORMATION_STREAM as KInfoStream,
    KEYWORDS_STREAM as KKeyStream,
)

KSheetFormatProperty = "SW-All Sheet Format Data"


@dataclass(frozen=True, slots=True)
class DrawingView:
    Name: str
    ModelPath: str
    Description: str


@dataclass(frozen=True, slots=True)
class DrawingSheet:
    Name: str
    PaperSize: str
    ScaleNumerator: float
    ScaleDenominator: float
    WidthMetres: float
    HeightMetres: float
    Views: tuple[DrawingView, ...]


@dataclass(frozen=True, slots=True)
class DrawingRef:
    Name: str
    Description: str


@dataclass(frozen=True, slots=True)
class DrawingData:
    Name: str
    Sheets: tuple[DrawingSheet, ...]
    References: tuple[DrawingRef, ...]
    Notes: tuple[str, ...]
    SourcePath: str


def LocalName(Value: str) -> str:
    return Value.rsplit("}", 1)[-1]


def XmlRoot(DataValue: bytes) -> XmlTree.Element:
    Start = DataValue.find(b"<")
    if Start < 0:
        raise SldprtFormatError("drawing XML has no root element")
    try:
        return XmlTree.fromstring(DataValue[Start:])
    except XmlTree.ParseError as ErrorInfo:
        raise SldprtFormatError(f"drawing XML is malformed: {ErrorInfo}") from ErrorInfo


def TextValue(Element: XmlTree.Element | None, Default: str = "") -> str:
    if Element is None or Element.text is None:
        return Default
    return Element.text.strip()


def FloatValue(Element: XmlTree.Element | None, LabelValue: str) -> float:
    TextData = TextValue(Element)
    try:
        return float(TextData)
    except ValueError as ErrorInfo:
        raise SldprtFormatError(
            f"drawing field {LabelValue!r} is not numeric: {TextData!r}"
        ) from ErrorInfo


def SheetFormats(DataValue: bytes) -> dict[str, tuple[float, float, float, float]]:
    RootValue = XmlRoot(DataValue)
    Result: dict[str, tuple[float, float, float, float]] = {}
    for Element in RootValue.iter():
        if LocalName(Element.tag) != "property":
            continue
        if Element.attrib.get("name") != KSheetFormatProperty:
            continue
        TextData = TextValue(Element.find("{*}lpstr")) or TextValue(Element)
        for RowValue in TextData.split("@@"):
            Fields = RowValue.split("@")
            if len(Fields) < 6 or not Fields[0]:
                continue
            try:
                Result[Fields[0]] = (
                    float(Fields[2]),
                    float(Fields[3]),
                    float(Fields[4]),
                    float(Fields[5]),
                )
            except ValueError as ErrorInfo:
                raise SldprtFormatError(
                    f"drawing sheet format is not numeric: {RowValue!r}"
                ) from ErrorInfo
    return Result


def ReadView(Element: XmlTree.Element) -> DrawingView:
    ViewName = Element.attrib.get("Name", "")
    ModelPath = TextValue(Element)
    if not ViewName or not ModelPath:
        raise SldprtFormatError("drawing sheet has an incomplete view")
    return DrawingView(ViewName, ModelPath, Element.attrib.get("Description", ""))


def ReadSheet(
    Element: XmlTree.Element, Formats: dict[str, tuple[float, float, float, float]]
) -> DrawingSheet:
    SheetName = Element.attrib.get("Name", "")
    if not SheetName:
        raise SldprtFormatError("drawing sheet has no name")
    FormatData = Formats.get(SheetName)
    if FormatData is None:
        raise SldprtFormatError(f"drawing sheet {SheetName!r} has no format data")
    PaperSize = ""
    Numerator = 1.0
    Denominator = 1.0
    Views: list[DrawingView] = []
    for ChildValue in Element:
        ChildTag = LocalName(ChildValue.tag)
        if ChildTag == "PaperSize":
            PaperSize = ChildValue.attrib.get("Description", "")
        elif ChildTag == "ScaleNumerator":
            Numerator = FloatValue(ChildValue, "ScaleNumerator")
        elif ChildTag == "ScaleDenominator":
            Denominator = FloatValue(ChildValue, "ScaleDenominator")
        elif ChildTag == "View":
            Views.append(ReadView(ChildValue))
    WidthValue, HeightValue, FormatNumerator, FormatDenominator = FormatData
    if FormatNumerator > 0.0 and FormatDenominator > 0.0:
        Numerator, Denominator = FormatNumerator, FormatDenominator
    return DrawingSheet(
        SheetName,
        PaperSize,
        Numerator,
        Denominator,
        WidthValue,
        HeightValue,
        tuple(Views),
    )


def ReadSheets(
    RootValue: XmlTree.Element, Formats: dict[str, tuple[float, float, float, float]]
) -> tuple[DrawingSheet, ...]:
    return tuple(
        ReadSheet(Element, Formats)
        for Element in RootValue.iter()
        if LocalName(Element.tag) == "Sheet" and Element.attrib.get("Type") == "Sheet"
    )


def ReadReferences(RootValue: XmlTree.Element) -> tuple[DrawingRef, ...]:
    return tuple(
        DrawingRef(
            Element.attrib.get("Name", ""),
            Element.attrib.get("Description", ""),
        )
        for Element in RootValue.iter()
        if LocalName(Element.tag) == "Reference"
    )


def ReadNotes(RootValue: XmlTree.Element) -> tuple[str, ...]:
    return tuple(
        NoteValue
        for Element in RootValue.iter()
        if LocalName(Element.tag) == "Note"
        for NoteValue in (Element.text or "",)
        if NoteValue.strip()
    )


def ReadDrawing(
    Source: str | FilePath | bytes, IncludeGeometry: bool = False
) -> DrawingData:
    if IncludeGeometry:
        raise SldprtFormatError(
            "drawing view geometry is not supported; only sheet metadata is available"
        )
    if isinstance(Source, bytes):
        Archive = SldprtArchive.from_bytes(Source, "drawing")
        SourcePath = ""
    else:
        PathValue = FilePath(Source).expanduser().resolve()
        Archive = SldprtArchive.open(PathValue)
        SourcePath = str(PathValue)
    Keywords = Archive.get(KKeyStream)
    Information = Archive.get(KInfoStream)
    if Keywords is None:
        raise SldprtFormatError(f"drawing is missing {KKeyStream}")
    if Information is None:
        raise SldprtFormatError(f"drawing is missing {KInfoStream}")
    RootValue = XmlRoot(Keywords)
    if LocalName(RootValue.tag) != "Keywords":
        raise SldprtFormatError("drawing keywords root is not Keywords")
    NameValue = RootValue.attrib.get("Name", "")
    if not NameValue:
        raise SldprtFormatError("drawing has no name")
    Sheets = ReadSheets(RootValue, SheetFormats(Information))
    if not Sheets:
        raise SldprtFormatError("drawing has no sheets")
    return DrawingData(
        NameValue,
        Sheets,
        ReadReferences(RootValue),
        ReadNotes(RootValue),
        SourcePath,
    )
