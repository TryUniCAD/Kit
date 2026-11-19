from dataclasses import replace as ReplaceValue
from json import loads as LoadJson
from pathlib import Path as FilePath

from convert import open_document as OpenDoc
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Records.RecordSource import CadSource
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from tests.Convert.Commands.CliProcess import CliProcess


# normal command conversion must route a complete typed drawing through the native writer
def CheckBlankDrawingConvert(TmpPath: FilePath) -> None:
    Sheet = DrawingSheet("page", "Installation sheet", 0.2794, 0.2159, (5, 7))
    Document = CadDocument(
        CadSource("interchange.json", "", "0" * 64),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        units=UnitSystem.KMeter,
        DrawingValue=DrawingData(Sheet.EntityId, (Sheet,)),
    )
    Source = TmpPath / "layout.json"
    Authored = Document.to_json()
    _ = Source.write_text(Authored, encoding="utf-8")
    for Name, FormatArgs in (
        ("default.SLDDRW", ()),
        ("explicit.SLDDRW", ("--to", "solidworks.slddrw")),
    ):
        Target = TmpPath / Name
        Result = CliProcess(
            TmpPath, "convert", str(Source), str(Target), "--json", *FormatArgs
        )
        assert Result.returncode == 0, Result.stderr
        Report = LoadJson(Result.stdout)
        assert Report["destination_format"] == "solidworks.slddrw"
        assert Report["vendor_loadable"] is True and Report["dropped"] == []
        Drawing = OpenDoc(Target, strict=False).DrawingValue
        assert Drawing is not None and not Drawing.ModelRefs
        (Actual,) = Drawing.Sheets
        assert (
            Actual.EntityName,
            Actual.SheetWidth,
            Actual.SheetHeight,
            Actual.ScaleRatio,
        ) == (Sheet.EntityName, Sheet.SheetWidth, Sheet.SheetHeight, Sheet.ScaleRatio)
    assert Source.read_text(encoding="utf-8") == Authored
    Unsupported = ReplaceValue(Sheet, SheetWidth=0.297, SheetHeight=0.21)
    _ = Source.write_text(
        ReplaceValue(
            Document, DrawingValue=DrawingData(Unsupported.EntityId, (Unsupported,))
        ).to_json(),
        encoding="utf-8",
    )
    Existing = Target.read_bytes()
    Rejected = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--json", "--overwrite"
    )
    assert Rejected.returncode == 1
    assert LoadJson(Rejected.stderr)["error"] == "AdapterNotFoundError"
    assert Target.read_bytes() == Existing
