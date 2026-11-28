from hashlib import sha256 as HashBytes
import json as JsonLib
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory

from pytest import mark as MarkTests

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Integration.Fusion.Offsets.CheckOffsetRead import CheckOffsetRead
from tests.Convert.Integration.Fusion.Offsets.OffsetCase import OffsetCase
from tests.Convert.Integration.Fusion.Offsets.ReadOffsetCases import ReadOffsetCases


# installed command semantics must expose the same complete reader graph as the sdk
@MarkTests.parametrize("Sample", ReadOffsetCases())
def CheckOffsetCli(Sample: OffsetCase) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    assert HashBytes(Sample.Source.read_bytes()).hexdigest() == Sample.Digest
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    with TemporaryDirectory() as WorkName:
        Output = FilePath(WorkName) / "Decoded.json"
        Result = ProcessLayer.run(
            [
                System.executable,
                "-m",
                "KitCli",
                "decode",
                str(Sample.Source),
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
        Record = JsonLib.loads(Output.read_text())
        assert Record["partial"] is False and Record["layer"] == "neutral"
        Document = CadDocument.from_json(JsonLib.dumps(Record["document"]))
        CheckOffsetRead(Document, Sample)
