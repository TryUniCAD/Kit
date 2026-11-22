from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDir

from pytest import raises as RaisesError

from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.Commands.BuildParser import BuildParser
from convert.Commands.CliOptions import CliOptions
from convert.Commands.RunCommand import RunCommand
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc
from tests.Convert.Solidworks.PlainWriting.VerifyCliMeas import VerifyCliMeas


# the ordinary cli has no switch that publishes a candidate without evidence
def TestCandidate() -> None:
    with TempDir() as FolderName:
        Folder = FilePath(FolderName)
        Source = Folder / "Neutral.json"
        Target = Folder / "Candidate.SLDPRT"
        Document = MakePlainDoc("Candidate", ((0.0, 0.0), (12.0, 0.0), (2.0, 9.0)), 4.0)
        _ = Source.write_text(Document.to_json(), encoding="utf-8")
        _ = Target.write_bytes(b"previous output")
        Parser = BuildParser("0.0.0")
        Arguments = ["convert", str(Source), str(Target), "--json", "--overwrite"]
        Options = CliOptions()
        _ = Parser.parse_args(Arguments, namespace=Options)
        with RaisesError(ValueError, match="offline native measurement receipt"):
            RunCommand(Options)
        with RaisesError(SystemExit):
            _ = Parser.parse_args(
                [*Arguments, "--allow-unverified-native"], namespace=CliOptions()
            )
        assert Target.read_bytes() == b"previous output"
        RefuseBadLoops(Source, Target, Options, b"previous output")
        assert set(Folder.iterdir()) == {Source, Target}


# the ordinary command must publish exact measured bytes on both host path branches
def TestMeasuredCli() -> None:
    for RoleName in ("Skew", "Step"):
        with TempDir() as FolderName:
            VerifyCliMeas(FilePath(FolderName), RoleName)


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
            ["convert", str(Source), str(Target), "--overwrite"],
            namespace=Options,
        )
        with RaisesError(NotFoundError, match="does not support the destination"):
            RunCommand(Options)
        assert Marker.read_bytes() == b"protected measurements"
        assert set(Folder.iterdir()) == {Source, Target}
