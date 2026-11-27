import json as JsonLib
from os import pathsep as PathSeparator
from pathlib import Path

from pytest import mark as MarkTests, MonkeyPatch as PatchScope

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Integration.Fusion.DualSide.Admission.CheckAdmitDoc import (
    CheckAdmitDoc,
)
from tests.Convert.Integration.Fusion.DualSide.Admission.CheckWorldDoc import (
    CheckWorldDoc,
)
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# ordinary cli decoding must preserve measured world placement for discovery and held out source frames
@MarkTests.parametrize("CaseName", ("frame", "holdout_a", "holdout_a_restored"))
def CheckWorldCli(TmpPath: Path, MonkeyPatch: PatchScope, CaseName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == CaseName)
    RootPath = Path(__file__).resolve().parents[6]
    MonkeyPatch.setenv(
        "PYTHONPATH", PathSeparator.join((str(RootPath / "src"), str(RootPath / "Cli")))
    )
    Output = TmpPath / "Decoded.json"
    Result = CliProcess(TmpPath, "decode", str(Sample.Source), "--output", str(Output))
    assert Result.returncode == 0, Result.stderr
    Record = JsonLib.loads(Output.read_text())
    assert Record["partial"] is False and Record["layer"] == "neutral"
    Document = CadDocument.from_json(JsonLib.dumps(Record["document"]))
    CheckAdmitDoc(Document, Sample)
    CheckWorldDoc(Document, Sample)
    Target = TmpPath / "Unqualified.f3d"
    _ = Target.write_bytes(b"existing destination")
    Refusal = CliProcess(
        TmpPath, "convert", str(Sample.Source), str(Target), "--overwrite", "--json"
    )
    assert Refusal.returncode != 0 and "Traceback" not in Refusal.stderr
    assert Target.read_bytes() == b"existing destination"
