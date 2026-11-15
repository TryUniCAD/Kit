from __future__ import annotations

from pathlib import Path as FilePath

import pytest as PytestLib

from convert import open_document as OpenDocument
from convert.adapters.solidworks.container.Container import (
    BuildSldprt as BuildArchive,
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.drawing import DrawingData, ReadDrawing

# tracked drawings prove the reader against real solidworks authored sheets
KDrawRoot = (
    FilePath(__file__).resolve().parents[4]
    / "re"
    / "solidworks"
    / "examples"
    / "Drawings"
)

# one expected shape per tracked drawing keeps every assertion in one place
KExpected = {
    "angled.SLDDRW": ("Draw3", 1.0, 1.0, 3, "poly5b.sldprt"),
    "minimal.SLDDRW": ("Draw2", 2.0, 1.0, 2, "poly5deep.sldprt"),
    "standard.SLDDRW": ("Draw1", 2.0, 1.0, 4, "poly5a.sldprt"),
}


# every tracked drawing must open through the public drawing entry point
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestOpen() -> None:
    for NameValue in sorted(KExpected):
        DataValue = ReadDrawing(KDrawRoot / NameValue)
        assert isinstance(DataValue, DrawingData)
        assert DataValue.Name == KExpected[NameValue][0]
        assert DataValue.SourcePath.endswith(NameValue)


# sheet geometry and view composition must match what solidworks authored
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestSheet() -> None:
    for NameValue, Expected in KExpected.items():
        DataValue = ReadDrawing(KDrawRoot / NameValue)
        assert len(DataValue.Sheets) == 1
        SheetValue = DataValue.Sheets[0]
        assert SheetValue.Name == "Sheet1"
        assert SheetValue.PaperSize == "0"
        assert SheetValue.WidthMetres == PytestLib.approx(0.2794)
        assert SheetValue.HeightMetres == PytestLib.approx(0.2159)
        assert SheetValue.ScaleNumerator == PytestLib.approx(Expected[1])
        assert SheetValue.ScaleDenominator == PytestLib.approx(Expected[2])
        assert len(SheetValue.Views) == Expected[3]
        for ViewValue in SheetValue.Views:
            assert ViewValue.ModelPath.casefold().endswith(Expected[4])


# notes and references are the only recovered drawing text outside sheets
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestText() -> None:
    for NameValue in sorted(KExpected):
        DataValue = ReadDrawing(KDrawRoot / NameValue)
        assert len(DataValue.Notes) == 1
        assert DataValue.Notes[0].startswith("Kit five-line pad")
        assert DataValue.References
        assert any((ItemValue.Description for ItemValue in DataValue.References))


# authored note whitespace is part of the drawing text and must survive reading
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestNote() -> None:
    SourcePath = KDrawRoot / "standard.SLDDRW"
    SourceBytes = SourcePath.read_bytes()
    Streams = SldprtArchive.from_bytes(SourceBytes).streams
    Padded = Streams["swXmlContents/KeyWords"].replace(
        b">Kit five-line pad / standard views<", b">  padded note  <"
    )
    assert Padded != Streams["swXmlContents/KeyWords"]
    BlobValue = BuildArchive(
        {**Streams, "swXmlContents/KeyWords": Padded}, Template=SourceBytes
    )
    DataValue = ReadDrawing(BlobValue)
    assert DataValue.Notes == ("  padded note  ",)


# requesting unavailable view geometry must fail instead of returning metadata
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestGeom() -> None:
    with PytestLib.raises(SldprtFormatError):
        _ = ReadDrawing(KDrawRoot / "standard.SLDDRW", IncludeGeometry=True)


# a truncated or inconsistent drawing archive must never be read partially
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestFail() -> None:
    SourcePath = KDrawRoot / "standard.SLDDRW"
    SourceBytes = SourcePath.read_bytes()
    Streams = SldprtArchive.from_bytes(SourceBytes).streams
    InfoBytes = Streams["docProps/ISolidWorksInformation.xml"]
    Cases = (
        {
            KeyValue: Value
            for KeyValue, Value in Streams.items()
            if KeyValue != "swXmlContents/KeyWords"
        },
        {
            KeyValue: Value
            for KeyValue, Value in Streams.items()
            if KeyValue != "docProps/ISolidWorksInformation.xml"
        },
        {**Streams, "swXmlContents/KeyWords": b"<Keywords"},
        {**Streams, "swXmlContents/KeyWords": b'<Other Name="Draw9"/>'},
        {
            **Streams,
            "docProps/ISolidWorksInformation.xml": InfoBytes.replace(
                b"Sheet1@0.000000", b"Other@0.000000"
            ),
        },
        {**Streams, "swXmlContents/KeyWords": b'<Keywords Name="Draw9"/>'},
    )
    for StreamValue in Cases:
        BlobValue = BuildArchive(StreamValue, Template=SourceBytes)
        with PytestLib.raises(SldprtFormatError):
            _ = ReadDrawing(BlobValue)


# drawing writes stay rejected until the native grammar is recovered
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestWrite() -> None:
    for NameValue in sorted(KExpected):
        with PytestLib.raises(SldprtFormatError):
            _ = OpenDocument(KDrawRoot / NameValue)
