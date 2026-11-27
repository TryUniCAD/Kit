import json as JsonLib
from os import pathsep as PathSeparator
from pathlib import Path

from pytest import mark as MarkTests, MonkeyPatch as PatchScope

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Integration.Fusion.DualSide.Admission.CheckAdmitDoc import (
    CheckAdmitDoc,
)
from tests.Convert.Integration.Fusion.DualSide.Admission.ReadAdmitCases import (
    ReadAdmitCases,
)


# ordinary cli decoding exposes both controls while unsupported conversion remains atomic
@MarkTests.parametrize("CaseName", ("baseline", "holdout_b", "holdout_b_restored"))
def CheckDualCli(TmpPath: Path, MonkeyPatch: PatchScope, CaseName: str) -> None:
    Sample = next(Value for Value in ReadAdmitCases() if Value.Identity == CaseName)
    RootPath = Path(__file__).resolve().parents[6]
    MonkeyPatch.setenv(
        "PYTHONPATH", PathSeparator.join((str(RootPath / "src"), str(RootPath / "Cli")))
    )
    Output = TmpPath / "Decoded.json"
    Result = CliProcess(TmpPath, "decode", str(Sample.Source), "--output", str(Output))
    assert Result.returncode == 0, Result.stderr
    Record = JsonLib.loads(Output.read_text())
    assert Record["partial"] is False and Record["layer"] == "neutral"
    CheckAdmitDoc(CadDocument.from_json(JsonLib.dumps(Record["document"])), Sample)
    Target = TmpPath / "Unqualified.f3d"
    _ = Target.write_bytes(b"existing destination")
    Refusal = CliProcess(
        TmpPath, "convert", str(Sample.Source), str(Target), "--overwrite", "--json"
    )
    assert Refusal.returncode != 0 and "Traceback" not in Refusal.stderr
    assert Target.read_bytes() == b"existing destination"
