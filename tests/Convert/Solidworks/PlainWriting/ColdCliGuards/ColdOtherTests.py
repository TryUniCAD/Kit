from io import BytesIO
from json import loads as LoadJson
from pathlib import Path as FilePath
from os import pathsep as PathSeparator

from pytest import mark as TestMark, raises as RaisesError, MonkeyPatch as PatchScope

from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.PlainWriting.MakeColdSource import MakeColdSource


# qualification for one measured part writer cannot authorize a different export route
@TestMark.parametrize("RoleName", ("Skew", "Step"))
def CheckOtherCold(TmpPath: FilePath, RoleName: str, MonkeyPatch: PatchScope) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    MonkeyPatch.setenv(
        "PYTHONPATH", PathSeparator.join((str(RootPath / "src"), str(RootPath / "Cli")))
    )
    Source, _, _, _ = MakeColdSource(TmpPath, RoleName)
    Document = OpenDocument(Source)
    Stream = BytesIO(b"preserved stream")
    with RaisesError(ValueError, match="native-only feature"):
        _ = WriteDocument(
            Document, Stream, DestFormat="interchange.json", AllowCarrier=False
        )
    assert Stream.getvalue() == b"preserved stream" and Stream.tell() == 0
    Target = TmpPath / "Unqualified.json"
    _ = Target.write_bytes(b"preserved destination")
    Outcome = CliProcess(
        TmpPath,
        "convert",
        str(Source),
        str(Target),
        "--overwrite",
        "--json",
        "--to",
        "interchange.json",
    )
    assert Outcome.returncode != 0 and "Traceback" not in Outcome.stderr
    assert (
        "NativeFeature records are not conversion-ready"
        in LoadJson(Outcome.stderr)["message"]
    )
    assert Target.read_bytes() == b"preserved destination"
    assert set(TmpPath.iterdir()) == {Source, Target}
