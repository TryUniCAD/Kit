from __future__ import annotations

from pathlib import Path as FilePath
import struct as Struct

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


# recovered view positions must match the locations used to author each view
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestPos() -> None:
    Expected = {
        "standard.SLDDRW": {
            ("Sheet1", "Drawing View1"): (0.11, 0.23),
            ("Sheet1", "Drawing View2"): (0.22, 0.11),
            ("Sheet1", "Drawing View3"): (0.11, 0.23),
            ("Sheet1", "Drawing View4"): (0.22, 0.23),
        },
        "minimal.SLDDRW": {
            ("Sheet1", "Drawing View1"): (0.16, 0.16),
            ("Sheet1", "Drawing View2"): (0.16, 0.25),
        },
        "angled.SLDDRW": {
            ("Sheet1", "Drawing View1"): (0.12, 0.23),
            ("Sheet1", "Drawing View2"): (0.24, 0.23),
            ("Sheet1", "Drawing View3"): (0.12, 0.12),
        },
        "projected.SLDDRW": {
            ("Sheet1", "Drawing View1"): (0.10, 0.15),
            ("Sheet1", "Drawing View2"): (0.20, 0.15),
        },
        "multisheet.SLDDRW": {
            ("Sheet1", "Drawing View1"): (0.11, 0.23),
            ("Sheet2", "Drawing View2"): (0.16, 0.16),
        },
        "large.SLDDRW": {
            ("Sheet1", "Drawing View1"): (1.10, 0.40),
        },
        "coincident.SLDDRW": {
            ("Sheet1", "Drawing View1"): (0.11, 0.23),
            ("Sheet2", "Drawing View2"): (0.11, 0.23),
        },
    }
    for NameValue, PositionData in Expected.items():
        DataValue = ReadDrawing(KDrawRoot / NameValue, IncludePositions=True)
        Actual = {
            (SheetValue.Name, ViewValue.Name): (
                ViewValue.PositionX,
                ViewValue.PositionY,
            )
            for SheetValue in DataValue.Sheets
            for ViewValue in SheetValue.Views
        }
        assert set(Actual) == set(PositionData)
        for KeyValue, ItemValue in PositionData.items():
            assert Actual[KeyValue][0] == PytestLib.approx(ItemValue[0])
            assert Actual[KeyValue][1] == PytestLib.approx(ItemValue[1])


# recovered outline bounds must match the vendor view bounding boxes
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestBounds() -> None:
    Expected = {
        "standard.SLDDRW": {
            ("Sheet1", "Drawing View1"): (
                0.058682,
                0.193682,
                0.161318,
                0.266318,
            ),
            ("Sheet1", "Drawing View2"): (
                0.168682,
                0.096682,
                0.271318,
                0.123318,
            ),
            ("Sheet1", "Drawing View3"): (
                0.096682,
                0.193682,
                0.123318,
                0.266318,
            ),
            ("Sheet1", "Drawing View4"): (
                0.176084020253553,
                0.17669326688862,
                0.263915979746447,
                0.28330673311138,
            ),
        },
        "minimal.SLDDRW": {
            ("Sheet1", "Drawing View1"): (
                0.108682,
                0.123682,
                0.211318,
                0.196318,
            ),
            ("Sheet1", "Drawing View2"): (
                0.108682,
                0.228682,
                0.211318,
                0.271318,
            ),
        },
        "angled.SLDDRW": {
            ("Sheet1", "Drawing View1"): (
                0.089182,
                0.202182,
                0.150818,
                0.257818,
            ),
            ("Sheet1", "Drawing View2"): (
                0.229182,
                0.202182,
                0.250818,
                0.257818,
            ),
            ("Sheet1", "Drawing View3"): (
                0.092347476220844,
                0.0830225570756102,
                0.147652523779156,
                0.15697744292439,
            ),
        },
        "projected.SLDDRW": {
            ("Sheet1", "Drawing View1"): (
                0.048682,
                0.113682,
                0.151318,
                0.186318,
            ),
            ("Sheet1", "Drawing View2"): (
                0.186682,
                0.113682,
                0.213318,
                0.186318,
            ),
        },
        "multisheet.SLDDRW": {
            ("Sheet1", "Drawing View1"): (
                0.058682,
                0.193682,
                0.161318,
                0.266318,
            ),
            ("Sheet2", "Drawing View2"): (
                0.108682,
                0.146682,
                0.211318,
                0.173318,
            ),
        },
        "large.SLDDRW": {
            ("Sheet1", "Drawing View1"): (
                1.048682,
                0.363682,
                1.151318,
                0.436318,
            ),
        },
        "coincident.SLDDRW": {
            ("Sheet1", "Drawing View1"): (
                0.058682,
                0.193682,
                0.161318,
                0.266318,
            ),
            ("Sheet2", "Drawing View2"): (
                0.058682,
                0.216682,
                0.161318,
                0.243318,
            ),
        },
    }
    for NameValue, BoundsData in Expected.items():
        DataValue = ReadDrawing(KDrawRoot / NameValue, IncludePositions=True)
        Actual = {
            (SheetValue.Name, ViewValue.Name): (
                ViewValue.OutlineMinX,
                ViewValue.OutlineMinY,
                ViewValue.OutlineMaxX,
                ViewValue.OutlineMaxY,
            )
            for SheetValue in DataValue.Sheets
            for ViewValue in SheetValue.Views
        }
        assert set(Actual) == set(BoundsData)
        for KeyValue, ItemValue in BoundsData.items():
            for ActualValue, ExpectedValue in zip(
                Actual[KeyValue], ItemValue, strict=True
            ):
                assert ActualValue == PytestLib.approx(ExpectedValue)


# a display list whose position records disagree with the view list must fail
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestPosNo() -> None:
    SourcePath = KDrawRoot / "standard.SLDDRW"
    SourceBytes = SourcePath.read_bytes()
    Streams = SldprtArchive.from_bytes(SourceBytes).streams
    Original = Streams["Contents/DisplayLists"]
    Changed = Original.replace(Struct.pack("<d", 0.11), Struct.pack("<d", 5.0), 1)
    assert Changed != Original
    BlobValue = BuildArchive(
        {**Streams, "Contents/DisplayLists": Changed}, Template=SourceBytes
    )
    with PytestLib.raises(SldprtFormatError):
        _ = ReadDrawing(BlobValue, IncludePositions=True)


# requesting unavailable view geometry must fail instead of returning metadata
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestGeom() -> None:
    with PytestLib.raises(SldprtFormatError):
        _ = ReadDrawing(KDrawRoot / "standard.SLDDRW", IncludeGeometry=True)


# sheet format entries are not sheets and must not be decoded as ones
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestMulti() -> None:
    DataValue = ReadDrawing(KDrawRoot / "multisheet.SLDDRW")
    assert [ItemValue.Name for ItemValue in DataValue.Sheets] == ["Sheet2", "Sheet1"]
    FirstValue, SecondValue = DataValue.Sheets
    assert FirstValue.PaperSize == "12"
    assert FirstValue.ScaleNumerator == PytestLib.approx(2.0)
    assert FirstValue.ScaleDenominator == PytestLib.approx(1.0)
    assert len(FirstValue.Views) == 1
    assert SecondValue.PaperSize == "0"
    assert SecondValue.WidthMetres == PytestLib.approx(0.2794)
    assert len(SecondValue.Views) == 1
    assert "multi sheet note" in DataValue.Notes


# projected views carry the parent model path and must decode like base views
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestProj() -> None:
    DataValue = ReadDrawing(KDrawRoot / "projected.SLDDRW")
    assert DataValue.Name == "Draw2"
    assert len(DataValue.Sheets) == 1
    SheetValue = DataValue.Sheets[0]
    assert [ItemValue.Name for ItemValue in SheetValue.Views] == [
        "Drawing View1",
        "Drawing View2",
    ]
    for ViewValue in SheetValue.Views:
        assert ViewValue.ModelPath.casefold().endswith("poly5a.sldprt")


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
