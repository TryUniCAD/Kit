from hashlib import sha256 as HashBytes
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as MarkTests

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.CheckRimMeasure import (
    CheckRimMeasure,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.ReadRimApi import ReadRimApi


# fresh ordinary cli processes must expose the complete reader while preserving unqualified write refusal
@MarkTests.parametrize(
    "CaseName",
    ("source-discovery-01", "source-holdout-05", "depth-holdout-02", "fresh-03"),
)
def CheckRimCli(TmpPath: FilePath, CaseName: str) -> None:
    (Sample,) = (Value for Value in ReadPolicyCases() if Value.CaseName == CaseName)
    Output = TmpPath / "Decoded.json"
    Outcome = CliProcess(TmpPath, "decode", str(Sample.Source), "--output", str(Output))
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Record = LoadJson(Output.read_text())
    assert Record["partial"] is False and Record["layer"] == "neutral"
    Document = CadDocument.from_json(DumpJson(Record["document"]))
    Document.AssertValid()
    assert isinstance(Document.feature_timeline[-1].definition, RadiusFillet)
    assert Document.metadata["fusion.read_only"] is True
    CheckRimMeasure(Document, ReadRimApi(CaseName))
    Target = TmpPath / "Refused.f3d"
    _ = Target.write_bytes(b"preserved destination")
    Refusal = CliProcess(
        TmpPath, "convert", str(Sample.Source), str(Target), "--overwrite", "--json"
    )
    assert Refusal.returncode == 1 and not Refusal.stdout
    assert "conversion-ready" in LoadJson(Refusal.stderr)["message"]
    assert Target.read_bytes() == b"preserved destination"
    assert HashBytes(Sample.Source.read_bytes()).hexdigest() == Sample.Digest
