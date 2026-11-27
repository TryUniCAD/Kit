from dataclasses import replace as ChangeRecord
from json import loads as ParseJson
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts
from tests.Research.Archives.Comparison.BulkProcess import RunBulk
from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# zero coordinate geometry isolates physical topology quantities from unrelated rounded sketch coordinates
def MakeUnitModel(AreaValue: float, VolumeValue: float) -> CadDocument:
    Document = MakeDocument()
    DatumStep = Document.feature_timeline[0]
    BodyValue = ChangeRecord(
        Document.bodies[0],
        final_feature_id=DatumStep.id,
        topology=TopologyCounts(volume=VolumeValue, surface_area=AreaValue),
    )
    return ChangeRecord(
        Document,
        parameters=(),
        sketches=(),
        feature_timeline=(DatumStep,),
        bodies=(BodyValue,),
    )


# exact topology observations must normalize across feet without hiding genuine area or volume changes
@MarkValue.parametrize(
    "AreaValue,VolumeValue,ExitCode,StatusName",
    (
        (92903.04, 28316846.592, 0, "equal_observed_graph"),
        (92903.0401, 28316846.592, 2, "different"),
        (92903.04, 28316846.5921, 2, "different"),
    ),
)
def CheckFootUnits(
    TmpPath: FilePath,
    AreaValue: float,
    VolumeValue: float,
    ExitCode: int,
    StatusName: str,
) -> None:
    First = TmpPath / "Feet"
    Second = TmpPath / "Millimeters"
    First.mkdir()
    Second.mkdir()
    WriteDocument(First / "Part.json", MakeUnitModel(1.0, 1.0))
    WriteDocument(Second / "Part.json", MakeUnitModel(AreaValue, VolumeValue))
    Output = TmpPath / "Output"
    Result = RunBulk(
        [
            "--left",
            str(First),
            "--right",
            str(Second),
            "--left-unit",
            "ft",
            "--output",
            str(Output),
        ]
    )
    assert Result.returncode == ExitCode, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["outcomes"] == {StatusName: 1}
    assert set(Summary["absolute_tolerances"].values()) == {0}
    assert Summary["geometry_units"] == {"left": "ft", "right": "mm"}
