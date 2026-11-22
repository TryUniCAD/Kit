from contextlib import redirect_stdout as RedirectOutput
from hashlib import sha256 as CalcSha
from io import StringIO as StringIo
from json import dumps as DumpJson, loads as LoadJson
from os import name as OsName
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDir
from typing import cast as CastValue

from pytest import raises as RaisesError

from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.Commands.BuildParser import BuildParser
from convert.Commands.CliOptions import CliOptions
from convert.Commands.RunCommand import RunCommand
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc


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


# a trusted receipt permits the exact relocated standalone output on the host path branch
def TestMeasuredCli() -> None:
    if OsName == "nt":
        return
    with TempDir() as FolderName:
        Folder = FilePath(FolderName)
        Source = Folder / "Neutral.json"
        Target = Folder / "sdk factory skew.SLDPRT"
        ReceiptPath = Folder / "Measurement.json"
        Document, Envelope, Digest = MeasurePlainDoc("Skew")
        _ = Source.write_text(Document.to_json(), encoding="utf-8")
        _ = ReceiptPath.write_text(DumpJson(Envelope), encoding="utf-8")
        Options = CliOptions()
        _ = BuildParser("0.0.0").parse_args(
            [
                "convert",
                str(Source),
                str(Target),
                "--json",
                "--native-measurement",
                str(ReceiptPath),
            ],
            namespace=Options,
        )
        Output = StringIo()
        with RedirectOutput(Output):
            RunCommand(Options)
        Report = CastValue(dict[str, object], LoadJson(Output.getvalue()))
        Written = Target.read_bytes()
        assert Report["application_usable"] is Report["vendor_loadable"] is True
        assert Report["dropped"] == []
        assert Report["bytes_written"] == len(Written)
        assert CalcSha(Written).hexdigest() == Digest
        assert set(Folder.iterdir()) == {Source, Target, ReceiptPath}


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
