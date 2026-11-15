from __future__ import annotations

from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath
import struct as Struct

import pytest as PytestLib

from convert import open_document as OpenDocument
from convert.adapters.solidworks.container.Container import (
    BuildSldprt as BuildArchive,
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.drawing import DrawingData, ReadDrawing, WriteDrawing
from convert.adapters.solidworks.drawing.DefinitionObjects import ObjectBlocks
from convert.adapters.solidworks.drawing.DefinitionValues import (
    EncodeSheet,
    EncodeViewBlock,
    SheetRecordAt,
    ViewBlock,
)

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


# the definition sheet and view blocks must decode to the authored values
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestValues() -> None:
    Counts = {
        "angled.SLDDRW": 6,
        "minimal.SLDDRW": 5,
        "standard.SLDDRW": 7,
    }
    for NameValue, CountValue in Counts.items():
        DataValue = SldprtArchive.open(KDrawRoot / NameValue).require(
            "Contents/Definition"
        )
        SheetValue = ObjectBlocks(DataValue, "moDrSheet", "moRefPlane_c")[0]
        SheetRecord = SheetRecordAt(SheetValue.Values)
        assert SheetRecord.NameValue == "Sheet1"
        assert SheetRecord.Scale == PytestLib.approx(-2.0)
        assert SheetRecord.Count == CountValue
        assert EncodeSheet(SheetRecord)[2:] == SheetValue.Values[2:]
        ViewValue = ObjectBlocks(DataValue, "moView_c", "moSketchBlockMgr_c")[0]
        Records, TailValue = ViewBlock(ViewValue.Values)
        assert len(Records) == 10
        assert Records[0].NameValue == "*Full Sheet"
        assert [Record.NameValue for Record in Records[1:]] == ["Unused"] * 9
        assert [Record.Index for Record in Records] == list(range(10))
        assert EncodeViewBlock(Records, TailValue) == ViewValue.Values


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


# recovered model bounds must match the referenced part bounding box
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestModel() -> None:
    Expected = {
        "standard.SLDDRW": (
            (0.0185, 0.016, 0.0045),
            (-0.005, 0.0, 0.0),
            (0.042, 0.032, 0.009),
        ),
        "minimal.SLDDRW": (
            (0.0185, 0.016, 0.0085),
            (-0.005, 0.0, 0.0),
            (0.042, 0.032, 0.017),
        ),
        "angled.SLDDRW": (
            (0.0185, 0.0135, 0.0065),
            (-0.008, -0.010, 0.0),
            (0.045, 0.037, 0.013),
        ),
        "projected.SLDDRW": (
            (0.0185, 0.016, 0.0045),
            (-0.005, 0.0, 0.0),
            (0.042, 0.032, 0.009),
        ),
        "multisheet.SLDDRW": (
            (0.0185, 0.016, 0.0045),
            (-0.005, 0.0, 0.0),
            (0.042, 0.032, 0.009),
        ),
        "large.SLDDRW": (
            (0.0185, 0.016, 0.0045),
            (-0.005, 0.0, 0.0),
            (0.042, 0.032, 0.009),
        ),
        "coincident.SLDDRW": (
            (0.0185, 0.016, 0.0045),
            (-0.005, 0.0, 0.0),
            (0.042, 0.032, 0.009),
        ),
    }
    for NameValue, BoundsData in Expected.items():
        DataValue = ReadDrawing(KDrawRoot / NameValue, IncludePositions=True)
        for SheetValue in DataValue.Sheets:
            for ViewValue in SheetValue.Views:
                Bounds = ViewValue.ModelBounds
                assert Bounds is not None
                for ActualValue, ExpectedValue in zip(
                    (Bounds.Center.x, Bounds.Center.y, Bounds.Center.z),
                    BoundsData[0],
                    strict=True,
                ):
                    assert ActualValue == PytestLib.approx(ExpectedValue)
                for ActualValue, ExpectedValue in zip(
                    (Bounds.Minimum.x, Bounds.Minimum.y, Bounds.Minimum.z),
                    BoundsData[1],
                    strict=True,
                ):
                    assert ActualValue == PytestLib.approx(ExpectedValue)
                for ActualValue, ExpectedValue in zip(
                    (Bounds.Maximum.x, Bounds.Maximum.y, Bounds.Maximum.z),
                    BoundsData[2],
                    strict=True,
                ):
                    assert ActualValue == PytestLib.approx(ExpectedValue)


# recovered model edges must match the vendor edge counts and first segment
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestEdge() -> None:
    Expected = {
        "standard.SLDDRW": {
            "Drawing View1": (5, (0.019, 0.032, 0.009)),
            "Drawing View2": (7, (0.042, 0.017, 0.009)),
            "Drawing View3": (7, (0.042, 0.017, 0.009)),
            "Drawing View4": (12, (0.042, 0.017, 0.009)),
        },
        "angled.SLDDRW": {
            "Drawing View1": (5, (0.012, 0.037, 0.013)),
            "Drawing View2": (7, (-0.008, 0.012, 0.013)),
            "Drawing View3": (10, (0.012, 0.037, 0.013)),
        },
        "projected.SLDDRW": {
            "Drawing View1": (5, (0.019, 0.032, 0.009)),
            "Drawing View2": (7, (0.042, 0.017, 0.009)),
        },
    }
    for NameValue, EdgeData in Expected.items():
        DataValue = ReadDrawing(KDrawRoot / NameValue, IncludeEdges=True)
        Actual = {
            ViewValue.Name: ViewValue.Edges
            for SheetValue in DataValue.Sheets
            for ViewValue in SheetValue.Views
        }
        assert set(Actual) == set(EdgeData)
        for ViewName, (CountValue, StartValue) in EdgeData.items():
            Edges = Actual[ViewName]
            assert len(Edges) == CountValue
            assert Edges[0].Start.x == PytestLib.approx(StartValue[0])
            assert Edges[0].Start.y == PytestLib.approx(StartValue[1])
            assert Edges[0].Start.z == PytestLib.approx(StartValue[2])


# a drawing without a complete edge block must fail instead of returning partial edges
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestEdgeNo() -> None:
    for NameValue in ("minimal.SLDDRW", "large.SLDDRW"):
        with PytestLib.raises(SldprtFormatError):
            _ = ReadDrawing(KDrawRoot / NameValue, IncludeEdges=True)


# the vendor transform is the only independent check on the recovered rotation
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestOrient() -> None:
    Expected = {
        "Drawing View1": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        "Drawing View2": (
            (1.0, 0.0, 0.0),
            (0.0, -3.5527136788005e-15, 1.0),
            (0.0, -1.0, -3.5527136788005e-15),
        ),
        "Drawing View3": (
            (-3.5527136788005e-15, 0.0, 1.0),
            (0.0, 1.0, 0.0),
            (-1.0, 0.0, -3.5527136788005e-15),
        ),
        "Drawing View4": (
            (0.7071067811865464, -0.4082040559113551, 0.5773815451999837),
            (0.0, 0.8165408118857499, 0.5772877120855426),
            (-0.7071067811865488, -0.4082040559113538, 0.5773815451999819),
        ),
    }
    DataValue = ReadDrawing(KDrawRoot / "standard.SLDDRW", IncludeSheetEdges=True)
    Actual = {
        ViewValue.Name: ViewValue.Orientation
        for SheetValue in DataValue.Sheets
        for ViewValue in SheetValue.Views
    }
    assert set(Actual) == set(Expected)
    for ViewName, MatrixData in Expected.items():
        Orientation = Actual[ViewName]
        assert Orientation is not None
        for RowIndex, RowData in enumerate(MatrixData):
            for ColumnIndex, ItemValue in enumerate(RowData):
                assert Orientation.Matrix[RowIndex][ColumnIndex] == PytestLib.approx(
                    ItemValue, abs=1e-09
                )


# one view drawings isolate each record so a wrong binding is visible
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestOrientOne() -> None:
    Expected = {
        "orient-front.SLDDRW": (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        "orient-top.SLDDRW": (
            (1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            (0.0, -1.0, 0.0),
        ),
        "orient-right.SLDDRW": (
            (0.0, 0.0, 1.0),
            (0.0, 1.0, 0.0),
            (-1.0, 0.0, 0.0),
        ),
        "orient-iso.SLDDRW": (
            (0.7071067811865464, -0.4082040559113551, 0.5773815451999837),
            (0.0, 0.8165408118857499, 0.5772877120855426),
            (-0.7071067811865488, -0.4082040559113538, 0.5773815451999819),
        ),
    }
    for NameValue, MatrixData in Expected.items():
        DataValue = ReadDrawing(KDrawRoot / NameValue, IncludeSheetEdges=True)
        ViewValue = DataValue.Sheets[0].Views[0]
        Orientation = ViewValue.Orientation
        assert Orientation is not None
        for RowIndex, RowData in enumerate(MatrixData):
            for ColumnIndex, ItemValue in enumerate(RowData):
                assert Orientation.Matrix[RowIndex][ColumnIndex] == PytestLib.approx(
                    ItemValue, abs=1e-09
                )
        assert ViewValue.SheetEdges


# the outline is the only independent check on the projected edges
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestSheetEdge() -> None:
    for NameValue in (
        "standard.SLDDRW",
        "angled.SLDDRW",
        "projected.SLDDRW",
        "multisheet.SLDDRW",
        "coincident.SLDDRW",
    ):
        DataValue = ReadDrawing(KDrawRoot / NameValue, IncludeSheetEdges=True)
        Paddings: set[float] = set()
        for SheetValue in DataValue.Sheets:
            for ViewValue in SheetValue.Views:
                assert ViewValue.SheetEdges
                assert len(ViewValue.SheetEdges) == len(ViewValue.Edges)
                XValues = [
                    ItemValue
                    for EdgeValue in ViewValue.SheetEdges
                    for ItemValue in (EdgeValue.Start.x, EdgeValue.End.x)
                ]
                YValues = [
                    ItemValue
                    for EdgeValue in ViewValue.SheetEdges
                    for ItemValue in (EdgeValue.Start.y, EdgeValue.End.y)
                ]
                assert ViewValue.OutlineMinX is not None
                assert ViewValue.OutlineMinY is not None
                assert ViewValue.OutlineMaxX is not None
                assert ViewValue.OutlineMaxY is not None
                assert min(XValues) >= ViewValue.OutlineMinX
                assert max(XValues) <= ViewValue.OutlineMaxX
                assert min(YValues) >= ViewValue.OutlineMinY
                assert max(YValues) <= ViewValue.OutlineMaxY
                LeftPad = min(XValues) - ViewValue.OutlineMinX
                RightPad = ViewValue.OutlineMaxX - max(XValues)
                assert LeftPad == PytestLib.approx(RightPad, abs=1e-09)
                assert LeftPad == PytestLib.approx(0.004318, abs=1e-09)
                Paddings.add(round(LeftPad, 9))
        assert len(Paddings) == 1


# the twin record is the only source of a custom view scale
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestScale() -> None:
    DataValue = ReadDrawing(KDrawRoot / "scale3.SLDDRW", IncludeSheetEdges=True)
    ViewValue = DataValue.Sheets[0].Views[0]
    assert ViewValue.ViewScale == PytestLib.approx(3.0)
    XValues = [
        ItemValue
        for EdgeValue in ViewValue.SheetEdges
        for ItemValue in (EdgeValue.Start.x, EdgeValue.End.x)
    ]
    YValues = [
        ItemValue
        for EdgeValue in ViewValue.SheetEdges
        for ItemValue in (EdgeValue.Start.y, EdgeValue.End.y)
    ]
    assert ViewValue.OutlineMinX is not None
    assert ViewValue.OutlineMaxX is not None
    assert ViewValue.OutlineMinY is not None
    assert ViewValue.OutlineMaxY is not None
    assert min(XValues) - ViewValue.OutlineMinX == PytestLib.approx(0.004318)
    assert ViewValue.OutlineMaxX - max(XValues) == PytestLib.approx(0.004318)
    assert min(YValues) >= ViewValue.OutlineMinY
    assert max(YValues) <= ViewValue.OutlineMaxY


# a missing record must fail closed rather than guess a rotation
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestSheetNo() -> None:
    for NameValue in ("minimal.SLDDRW", "large.SLDDRW"):
        with PytestLib.raises(SldprtFormatError):
            _ = ReadDrawing(KDrawRoot / NameValue, IncludeSheetEdges=True)


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


# the writer must round trip the recovered position and scale records
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestWriteView() -> None:
    SourcePath = KDrawRoot / "orient-front.SLDDRW"
    SourceBytes = SourcePath.read_bytes()
    DataValue = ReadDrawing(SourceBytes, IncludeSheetEdges=True)
    ViewValue = DataValue.Sheets[0].Views[0]
    NewView = ReplaceData(ViewValue, PositionX=0.15, PositionY=0.20, ViewScale=3.0)
    NewData = ReplaceData(
        DataValue,
        Sheets=(ReplaceData(DataValue.Sheets[0], Views=(NewView,)),),
    )
    BlobValue = WriteDrawing(SourceBytes, NewData)
    assert BlobValue != SourceBytes
    BackValue = ReadDrawing(BlobValue, IncludeSheetEdges=True)
    BackView = BackValue.Sheets[0].Views[0]
    assert BackView.PositionX == PytestLib.approx(0.15)
    assert BackView.PositionY == PytestLib.approx(0.20)
    assert BackView.ViewScale == PytestLib.approx(3.0)
    assert len(BackView.SheetEdges) == len(ViewValue.SheetEdges)
    assert ViewValue.OutlineMinX is not None
    assert ViewValue.OutlineMinY is not None
    assert ViewValue.PositionX is not None
    assert ViewValue.PositionY is not None
    assert BackView.OutlineMinX is not None
    assert BackView.OutlineMinY is not None
    Ratio = 3.0 / 2.0
    Padding = 0.004318
    assert BackView.OutlineMinX == PytestLib.approx(
        0.15 + (ViewValue.OutlineMinX - ViewValue.PositionX + Padding) * Ratio - Padding
    )
    assert BackView.OutlineMinY == PytestLib.approx(
        0.20 + (ViewValue.OutlineMinY - ViewValue.PositionY + Padding) * Ratio - Padding
    )


# the writer must bind records by creation index when keyword order differs
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestWriteOrder() -> None:
    SourceBytes = (KDrawRoot / "angled.SLDDRW").read_bytes()
    DataValue = ReadDrawing(SourceBytes, IncludeSheetEdges=True)
    Views = DataValue.Sheets[0].Views
    assert [ViewValue.Name for ViewValue in Views] != [
        "Drawing View1",
        "Drawing View2",
        "Drawing View3",
    ]
    NewViews = tuple(
        ReplaceData(ViewValue, PositionX=0.05 + 0.06 * Index, PositionY=0.10)
        for Index, ViewValue in enumerate(Views)
    )
    NewData = ReplaceData(
        DataValue, Sheets=(ReplaceData(DataValue.Sheets[0], Views=NewViews),)
    )
    BackValue = ReadDrawing(WriteDrawing(SourceBytes, NewData), IncludeSheetEdges=True)
    Actual = {
        ViewValue.Name: ViewValue.PositionX for ViewValue in BackValue.Sheets[0].Views
    }
    assert Actual["Drawing View1"] == PytestLib.approx(0.17)
    assert Actual["Drawing View2"] == PytestLib.approx(0.05)
    assert Actual["Drawing View3"] == PytestLib.approx(0.11)
    Reordered = ReplaceData(
        DataValue,
        Sheets=(ReplaceData(DataValue.Sheets[0], Views=tuple(reversed(NewViews))),),
    )
    ReorderedValue = ReadDrawing(
        WriteDrawing(SourceBytes, Reordered), IncludeSheetEdges=True
    )
    ReorderedActual = {
        ViewValue.Name: ViewValue.PositionX
        for ViewValue in ReorderedValue.Sheets[0].Views
    }
    assert ReorderedActual == Actual


# a renamed view must still receive the placement of its source record
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestWriteName() -> None:
    SourceBytes = (KDrawRoot / "orient-front.SLDDRW").read_bytes()
    DataValue = ReadDrawing(SourceBytes, IncludeSheetEdges=True)
    ViewValue = DataValue.Sheets[0].Views[0]
    NewView = ReplaceData(
        ViewValue, Name="My View", PositionX=-0.05, PositionY=-0.02, ViewScale=1.5
    )
    NewData = ReplaceData(
        DataValue, Sheets=(ReplaceData(DataValue.Sheets[0], Views=(NewView,)),)
    )
    BackValue = ReadDrawing(WriteDrawing(SourceBytes, NewData), IncludeSheetEdges=True)
    BackView = BackValue.Sheets[0].Views[0]
    assert BackView.PositionX == PytestLib.approx(-0.05)
    assert BackView.PositionY == PytestLib.approx(-0.02)
    assert BackView.ViewScale == PytestLib.approx(1.5)
    OriginView = ReplaceData(ViewValue, PositionX=0.0, PositionY=0.0, ViewScale=1.5)
    OriginData = ReplaceData(
        DataValue, Sheets=(ReplaceData(DataValue.Sheets[0], Views=(OriginView,)),)
    )
    OriginValue = ReadDrawing(
        WriteDrawing(SourceBytes, OriginData), IncludeSheetEdges=True
    )
    OriginBack = OriginValue.Sheets[0].Views[0]
    assert OriginBack.PositionX == PytestLib.approx(0.0)
    assert OriginBack.PositionY == PytestLib.approx(0.0)


# renaming more than one view is ambiguous and must fail closed
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestWriteMany() -> None:
    SourceBytes = (KDrawRoot / "standard.SLDDRW").read_bytes()
    DataValue = ReadDrawing(SourceBytes, IncludeSheetEdges=True)
    Views = tuple(
        ReplaceData(ViewValue, Name=f"View{Index}")
        for Index, ViewValue in enumerate(DataValue.Sheets[0].Views)
    )
    NewData = ReplaceData(
        DataValue, Sheets=(ReplaceData(DataValue.Sheets[0], Views=Views),)
    )
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDrawing(SourceBytes, NewData)


# coincident views must bind by creation index rather than record order
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestWriteSame() -> None:
    SourceBytes = (KDrawRoot / "coincident.SLDDRW").read_bytes()
    DataValue = ReadDrawing(SourceBytes, IncludeSheetEdges=True)
    Sheets = tuple(
        ReplaceData(
            SheetValue,
            Views=tuple(
                ReplaceData(
                    ViewValue,
                    PositionX=0.05 if ViewValue.Name == "Drawing View1" else 0.15,
                    PositionY=0.10,
                )
                for ViewValue in SheetValue.Views
            ),
        )
        for SheetValue in DataValue.Sheets
    )
    BackValue = ReadDrawing(
        WriteDrawing(SourceBytes, ReplaceData(DataValue, Sheets=Sheets)),
        IncludeSheetEdges=True,
    )
    Actual = {
        ViewValue.Name: ViewValue.PositionX
        for SheetValue in BackValue.Sheets
        for ViewValue in SheetValue.Views
    }
    assert Actual["Drawing View1"] == PytestLib.approx(0.05)
    assert Actual["Drawing View2"] == PytestLib.approx(0.15)


# repeated view names on different sheets must bind by sheet and view name
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestWriteSheet() -> None:
    SourceBytes = (KDrawRoot / "multisheet.SLDDRW").read_bytes()
    DataValue = ReadDrawing(SourceBytes, IncludeSheetEdges=True)
    Sheets = tuple(
        ReplaceData(
            SheetValue,
            Views=tuple(
                ReplaceData(ViewValue, PositionX=0.10, PositionY=0.10)
                for ViewValue in SheetValue.Views
            ),
        )
        for SheetValue in DataValue.Sheets
    )
    BackValue = ReadDrawing(
        WriteDrawing(SourceBytes, ReplaceData(DataValue, Sheets=Sheets)),
        IncludeSheetEdges=True,
    )
    for SheetValue in BackValue.Sheets:
        for ViewValue in SheetValue.Views:
            assert ViewValue.PositionX == PytestLib.approx(0.10)
            assert ViewValue.PositionY == PytestLib.approx(0.10)


# a view count that does not match the source records must fail closed
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestWriteNo() -> None:
    SourceBytes = (KDrawRoot / "orient-front.SLDDRW").read_bytes()
    DataValue = ReadDrawing(SourceBytes, IncludeSheetEdges=True)
    EmptyData = ReplaceData(
        DataValue, Sheets=(ReplaceData(DataValue.Sheets[0], Views=()),)
    )
    with PytestLib.raises(SldprtFormatError):
        _ = WriteDrawing(SourceBytes, EmptyData)


# drawing writes stay rejected until the native grammar is recovered
@PytestLib.mark.skipif(not KDrawRoot.is_dir(), reason="drawing corpus unavailable")
def TestWrite() -> None:
    for NameValue in sorted(KExpected):
        with PytestLib.raises(SldprtFormatError):
            _ = OpenDocument(KDrawRoot / NameValue)
