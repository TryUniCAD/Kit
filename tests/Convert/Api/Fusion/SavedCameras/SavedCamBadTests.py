from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as MarkTests

from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# invalid camera semantics must fail before the candidate can be published
@MarkTests.parametrize(
    "FieldName,FieldValue,Reason",
    (
        (
            "projection",
            2,
            "Unsupported named camera projection; expected stored code 1",
        ),
        ("up", [0.0, 1.0, 0.0], "Named camera view direction and up must span a plane"),
    ),
)
def TestCamMode(
    TmpPath: FilePath, FieldName: str, FieldValue: object, Reason: str
) -> None:
    Source = SavedSource(KSavedCases[0])
    Request = TmpPath / "Request.json"
    Prepare = RunParamStage(
        "PrepareRequest.py", Source, Request, ResearchFolder="SavedCameras"
    )
    assert Prepare.returncode == 0, Prepare.stderr
    Payload = CastValue(
        dict[str, object], LoadJson(Request.read_text(encoding="utf-8"))
    )
    Views = CastValue(list[dict[str, object]], Payload["named_views"])
    Camera = CastValue(dict[str, object], Views[0]["camera"])
    Camera[FieldName] = FieldValue
    _ = Request.write_text(DumpJson(Payload), encoding="utf-8")
    Candidate = TmpPath / "Candidate.f3d"
    Generate = RunParamStage(
        "GenerateSavedCuboid.py", Request, Candidate, ResearchFolder="SavedCameras"
    )
    assert Generate.returncode == 1 and not Candidate.exists()
    assert (
        Generate.stderr.strip()
        == f"Saved cuboid named-camera generation refused: {Reason}"
    )
