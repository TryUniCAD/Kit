from dataclasses import replace as ReplaceValue
from json import dumps as DumpJson, loads as LoadJson
from math import ulp as UnitInLastPlace
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
    Target = TmpPath / "explicit.SLDDRW"
    for Candidate, FormatArgs in (
        (TmpPath / "default.SLDDRW", ()),
        (Target, ("--to", "solidworks.slddrw")),
    ):
        Result = CliProcess(
            TmpPath, "convert", str(Source), str(Candidate), "--json", *FormatArgs
        )
        assert Result.returncode == 0, Result.stderr
        Report = LoadJson(Result.stdout)
        assert Report["destination_format"] == "solidworks.slddrw"
        assert Report["vendor_loadable"] is True and Report["dropped"] == []
        Strict = OpenDoc(Candidate)
        Drawing = Strict.DrawingValue
        assert Drawing is not None and not Drawing.ModelRefs
        assert Strict.diagnostics == ()
        assert (
            Strict.source.attributes[
                "solidworks.blank.complete_container_reconstruction"
            ]
            is True
        )
        Partial = OpenDoc(Candidate, strict=False)
        assert Partial.DrawingValue is not None and Partial.diagnostics
        (PartialSheet,) = Partial.DrawingValue.Sheets
        (Actual,) = Drawing.Sheets
        assert (
            Actual.EntityId,
            Actual.EntityName,
            Actual.ScaleRatio,
        ) == (PartialSheet.EntityId, Sheet.EntityName, Sheet.ScaleRatio)
        assert abs(Actual.SheetWidth - Sheet.SheetWidth) <= UnitInLastPlace(
            Sheet.SheetWidth
        )
        assert abs(Actual.SheetHeight - Sheet.SheetHeight) <= UnitInLastPlace(
            Sheet.SheetHeight
        )
    Strict = OpenDoc(Target)
    Decoded = CliProcess(TmpPath, "decode", str(Target))
    assert Decoded.returncode == 0, Decoded.stderr
    ReadBack = CadDocument.from_json(DumpJson(LoadJson(Decoded.stdout)["document"]))
    assert ReadBack.DrawingValue == Strict.DrawingValue
    assert ReadBack.source.attributes == Strict.source.attributes
    RewriteDecodedBlank(TmpPath, Target, ReadBack)
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


# the normal command must preserve strict source owners across native input and old neutral metadata
def RewriteDecodedBlank(
    TmpPath: FilePath, Source: FilePath, Document: CadDocument
) -> None:
    Original = Source.read_bytes()
    Neutral = LoadJson(Document.to_json())
    IntentKey = "solidworks.blank.intent"
    Intent = Neutral["source"]["attributes"][IntentKey]
    Sheet = Intent["DrawingValue"]["sheets"][0]
    assert "notes" not in Sheet

    LegacySource = TmpPath / "decoded-legacy.json"
    _ = LegacySource.write_text(DumpJson(Neutral), encoding="utf-8")
    ExplicitNullSource = TmpPath / "decoded-explicit-null.json"
    Sheet["notes"] = None
    _ = ExplicitNullSource.write_text(DumpJson(Neutral), encoding="utf-8")
    del Sheet["notes"]

    for Index, InputPath in enumerate((Source, LegacySource, ExplicitNullSource)):
        Target = TmpPath / f"Rewritten{Index}.SLDDRW"
        Result = CliProcess(TmpPath, "convert", str(InputPath), str(Target), "--json")
        assert Result.returncode == 0, Result.stderr
        Report = LoadJson(Result.stdout)
        assert Report["vendor_loadable"] is True and Report["dropped"] == []
        Reopened = OpenDoc(Target)
        assert Reopened.DrawingValue == Document.DrawingValue
        assert Reopened.metadata == Document.metadata
        ReopenedIntent = LoadJson(Reopened.to_json())["source"]["attributes"][IntentKey]
        assert ReopenedIntent.pop("FileValue") != Intent["FileValue"]
        assert ReopenedIntent == {
            Name: Value for Name, Value in Intent.items() if Name != "FileValue"
        }
    assert Source.read_bytes() == Original
