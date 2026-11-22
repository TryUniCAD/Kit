from contextlib import redirect_stdout as RedirectOutput
from io import StringIO as StringIo
from json import loads as LoadJson
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDir
from typing import cast as CastValue

from pytest import raises as RaisesError

from convert.adapters.base.UsabilityError import UsabilityError
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.Commands.BuildParser import BuildParser
from convert.Commands.CliOptions import CliOptions
from convert.Commands.RunCommand import RunCommand
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc


# the cli must retain strict publication while allowing a native candidate with explicit consent
def TestCandidate() -> None:
    with TempDir() as FolderName:
        Folder = FilePath(FolderName)
        Source = Folder / "Neutral.json"
        Target = Folder / "Candidate.SLDPRT"
        Document = MakePlainDoc("Candidate", ((0.0, 0.0), (12.0, 0.0), (2.0, 9.0)), 4.0)
        _ = Source.write_text(Document.to_json(), encoding="utf-8")
        Parser = BuildParser("0.0.0")
        Arguments = ["convert", str(Source), str(Target), "--json", "--overwrite"]
        _ = Target.write_bytes(b"previous output")
        Strict = CliOptions()
        _ = Parser.parse_args(Arguments, namespace=Strict)
        with RaisesError(UsabilityError, match="vendor_unloadable"):
            RunCommand(Strict)
        assert Target.read_bytes() == b"previous output"

        Candidate = CliOptions()
        _ = Parser.parse_args(
            [*Arguments, "--allow-unverified-native"], namespace=Candidate
        )
        Output = StringIo()
        with RedirectOutput(Output):
            RunCommand(Candidate)
        Report = CastValue(dict[str, object], LoadJson(Output.getvalue()))
        assert Report["application_usable"] is False
        assert Report["vendor_loadable"] is False
        assert Report["dropped"] == []
        Transfers = CastValue(list[dict[str, object]], Report["transfers"])
        assert Transfers and all(Transfer["mode"] == "native" for Transfer in Transfers)
        Written = Target.read_bytes()
        assert Report["bytes_written"] == len(Written)
        RefuseBadLoops(Source, Target, Candidate, Written)
        assert set(Folder.iterdir()) == {Source, Target}


# unsupported rings must fail selection while the prior native file stays intact
def RefuseBadLoops(
    Source: FilePath, Target: FilePath, Candidate: CliOptions, Written: bytes
) -> None:
    for Points in (
        ((0.0, 0.0), (6.0, 0.0), (12.0, 0.0), (2.0, 9.0)),
        ((0.0, 0.0), (1.0, 17.0), (3.0, 51.0), (0.0, 100.0)),
        tuple((float(Index), float(Index * Index)) for Index in range(65)),
    ):
        _ = Source.write_text(
            MakePlainDoc("Candidate", Points, 4.0).to_json(), encoding="utf-8"
        )
        with RaisesError(NotFoundError, match="does not support the destination"):
            RunCommand(Candidate)
        assert Target.read_bytes() == Written


# file overwrite authorization must protect a directory that has the part extension
def TestTargetDir() -> None:
    with TempDir() as FolderName:
        Folder = FilePath(FolderName)
        Source = Folder / "Neutral.json"
        Target = Folder / "Candidate.SLDPRT"
        Target.mkdir()
        Marker = Target / "measurements.json"
        _ = Marker.write_bytes(b"protected measurements")
        Document = MakePlainDoc("Candidate", ((0.0, 0.0), (12.0, 0.0), (2.0, 9.0)), 4.0)
        _ = Source.write_text(Document.to_json(), encoding="utf-8")
        Options = CliOptions()
        _ = BuildParser("0.0.0").parse_args(
            [
                "convert",
                str(Source),
                str(Target),
                "--allow-unverified-native",
                "--overwrite",
            ],
            namespace=Options,
        )
        with RaisesError(NotFoundError, match="does not support the destination"):
            RunCommand(Options)
        assert Marker.read_bytes() == b"protected measurements"
        assert set(Folder.iterdir()) == {Source, Target}
