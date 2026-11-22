from dataclasses import replace as ReplaceValue
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDir

from pytest import raises as RaisesError

from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.Commands.BuildParser import BuildParser
from convert.Commands.CliOptions import CliOptions
from convert.Commands.RunCommand import RunCommand
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.PlainWriting.LeaseMeasPath import LeaseMeasPath
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc
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
        RefuseBadSketch(Source, Target, Options, b"previous output")
        assert set(Folder.iterdir()) == {Source, Target}


# the ordinary command must publish exact measured bytes on both host path branches
def TestMeasuredCli() -> None:
    for RoleName in ("Skew", "Step"):
        with TempDir() as FolderName:
            VerifyCliMeas(FilePath(FolderName), RoleName)


# the installed command reports an invalid receipt home before any publication
def TestReceiptHome(TmpPath: FilePath) -> None:
    Source = TmpPath / "Neutral.json"
    Target = TmpPath / "Candidate.SLDPRT"
    Document = MakePlainDoc("Candidate", ((0.0, 0.0), (12.0, 0.0), (2.0, 9.0)), 4.0)
    _ = Source.write_text(Document.to_json(), encoding="utf-8")
    _ = Target.write_bytes(b"previous output")
    Outcome = CliProcess(
        TmpPath,
        "convert",
        str(Source),
        str(Target),
        "--json",
        "--overwrite",
        "--native-measurement",
        "~.__kit_missing_native_receipt_home__/Measurement.json",
    )
    assert Outcome.returncode == 1 and Outcome.stdout == ""
    assert (
        LoadJson(Outcome.stderr)["message"]
        == "native measurement receipt home directory is unavailable"
    )
    assert Target.read_bytes() == b"previous output"


# unsupported rings must fail selection while the prior native file stays intact
def RefuseBadSketch(
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
    Document = MakePlainDoc("Candidate", ((0.0, 0.0), (12.0, 0.0), (2.0, 9.0)), 4.0)
    SketchValue = Document.sketches[0]
    Relation = SketchRelation(
        "constraint/horizontal",
        ConstraintKind.KHorizontal,
        (ConstraintRef(SketchValue.entities[0].id),),
    )
    RelationDoc = ReplaceValue(
        Document, sketches=(ReplaceValue(SketchValue, constraints=(Relation,)),)
    )
    _ = Source.write_text(RelationDoc.to_json(), encoding="utf-8")
    with RaisesError(NotFoundError, match="does not support the destination"):
        RunCommand(Candidate)
    assert Target.read_bytes() == Written
    Driver = Parameter(
        "parameter/sketch/width",
        "D1",
        ParameterValue(12.0, ValueKind.KLength, "mm"),
        ParameterRole.KDriving,
        owner_id=SketchValue.id,
    )
    SketchValue = ReplaceValue(
        SketchValue,
        parameter_ids=(Driver.id,),
        constraints=(
            SketchRelation(
                "constraint/width",
                ConstraintKind.KDistance,
                (ConstraintRef(SketchValue.entities[0].id),),
                parameter_id=Driver.id,
            ),
        ),
    )
    Document = ReplaceValue(
        Document,
        parameters=(*Document.parameters, Driver),
        sketches=(SketchValue,),
    )
    _ = Source.write_text(Document.to_json(), encoding="utf-8")
    with RaisesError(NotFoundError, match="does not support the destination"):
        RunCommand(Candidate)
    assert Target.read_bytes() == Written


# a measured single file publication must preserve a populated directory at the final target
def TestTargetDir() -> None:
    with TempDir() as FolderName:
        Folder = FilePath(FolderName)
        Document, Envelope, _ = MeasurePlainDoc("Skew")
        Source = Folder / "Neutral.json"
        Evidence = Folder / "Measurement.json"
        _ = Source.write_text(Document.to_json(), encoding="utf-8")
        _ = Evidence.write_text(DumpJson(Envelope), encoding="utf-8")
        with LeaseMeasPath(Folder, f"{Document.metadata['name']}.SLDPRT") as Target:
            Target.mkdir()
            Marker = Target / "measurements.json"
            _ = Marker.write_bytes(b"protected measurements")
            try:
                RefuseTargetDir(Source, Evidence, Target)
                assert Marker.read_bytes() == b"protected measurements"
                assert set(Target.iterdir()) == {Marker}
                assert set(Target.parent.iterdir()) == (
                    {Source, Evidence, Target} if Target.parent == Folder else {Target}
                )
            finally:
                Marker.unlink(missing_ok=True)
                if Target.is_dir():
                    Target.rmdir()


# the receipt must qualify before the real cli publication reaches the directory conflict
def RefuseTargetDir(Source: FilePath, Evidence: FilePath, Target: FilePath) -> None:
    Options = CliOptions()
    _ = BuildParser("0.0.0").parse_args(
        [
            "convert",
            str(Source),
            str(Target),
            "--overwrite",
            "--native-measurement",
            str(Evidence),
        ],
        namespace=Options,
    )
    with RaisesError(OSError) as Failure:
        RunCommand(Options)
    assert Failure.value.filename2 == str(Target.resolve())
