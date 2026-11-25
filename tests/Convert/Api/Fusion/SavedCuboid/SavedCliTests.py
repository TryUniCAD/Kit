import json as JsonLib
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System

from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from interchange import CadDocument
from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# a fresh command process must decode the same complete saved graph as the public sdk
@MarkTests.parametrize("CaseValue", KSavedCases)
def TestSavedCli(TmpPath: FilePath, CaseValue: SavedCase) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    Source = SavedSource(CaseValue)
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    Output = TmpPath / "Decoded.json"
    Result = ProcessLayer.run(
        [
            System.executable,
            "-m",
            "KitCli",
            "decode",
            str(Source),
            "--output",
            str(Output),
        ],
        cwd=RootPath,
        env=Environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    Record = JsonLib.loads(Output.read_text(encoding="utf-8"))
    assert Record["partial"] is False and Record["layer"] == "neutral"
    Document = CadDocument.from_json(JsonLib.dumps(Record["document"]))
    assert Document == OpenDocument(Source)
    assert Document.metadata["fusion.read_only"] is True
