from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert.api.ApiOpen import OpenDocument
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Integration.Fusion.RimFillet.Public.MakePublicBad import (
    MakePublicBad,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.ReadPublicBads import (
    ReadPublicBads,
)


# sdk admission must reject every malformed complete archive after its actual native codec reopens it
@MarkTests.parametrize("Family, CaseName", ReadPublicBads())
def CheckNativeBad(TmpPath: FilePath, Family: str, CaseName: str) -> None:
    Encoded = MakePublicBad(Family, CaseName)
    Source = TmpPath / "Malformed.f3d"
    _ = Source.write_bytes(Encoded)
    assert ReadDocument(Encoded).Bodies
    with RaisesError(ValueError):
        _ = OpenDocument(Source)
    assert Source.read_bytes() == Encoded


# malformed native input must also fail a fresh ordinary conversion process without publishing bytes
@MarkTests.parametrize(
    "Family, CaseName, MessageText",
    (
        ("policy", "owner", "Native rim parameter binding has inconsistent owners"),
        (
            "geometry",
            "adjacent_faces",
            "Native rim recipe selects another physical edge or face",
        ),
        (
            "mass",
            "moiOffDiag:y",
            "Native circular mass cache disagrees with analytic geometry",
        ),
    ),
)
def CheckBadRimCli(
    TmpPath: FilePath, Family: str, CaseName: str, MessageText: str
) -> None:
    Source = TmpPath / "Malformed.f3d"
    _ = Source.write_bytes(MakePublicBad(Family, CaseName))
    Digest = HashBytes(Source.read_bytes()).hexdigest()
    Target = TmpPath / "Previous.f3d"
    _ = Target.write_bytes(b"preserved destination")
    Outcome = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--overwrite", "--json"
    )
    assert Outcome.returncode == 1 and not Outcome.stdout
    assert LoadJson(Outcome.stderr) == {"error": "ValueError", "message": MessageText}
    assert Target.read_bytes() == b"preserved destination"
    assert HashBytes(Source.read_bytes()).hexdigest() == Digest
