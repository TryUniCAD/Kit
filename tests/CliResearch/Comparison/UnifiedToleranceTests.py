from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.Comparison.UnifiedFixtures import MakeInputs
from tests.CliResearch.ResearchClient import ResearchCli


# tolerance agreement remains reportable without promoting an input to an exact agreement copy
def CheckTolerated(TmpPath: FilePath) -> None:
    Original = MakeInputs(TmpPath, IncludeIssues=False)
    Profile = {
        "length_mm": 0.1,
        "angle_rad": 0,
        "dimensionless": 0,
        "area_mm2": 0,
        "volume_mm3": 0,
    }
    _ = (TmpPath / "Tolerances.json").write_text(EncodeJson(Profile), encoding="utf-8")
    Reply = ResearchCli(
        TmpPath,
        "compare",
        "SolidWorks",
        "Fusion",
        "--unit",
        "mm",
        "--tolerances",
        "Tolerances.json",
        "-o",
        "Output",
    )
    assert Reply.returncode == 0, Reply.stderr + Reply.stdout
    Output = TmpPath / "Output"
    Summary = DecodeJson((Output / "summary.json").read_bytes())
    assert Summary["outcomes"] == {"equal_observed_graph": 1}
    assert Summary["absolute_tolerances"] == Profile
    assert Summary["unified"]["policy"] == "exact_equal_observed_graph"
    assert Summary["unified"]["count"] == 0
    assert Summary["pairs"][0]["unified"] is None
    assert not list((Output / "unified").iterdir())
    assert {InputPath: InputPath.read_bytes() for InputPath in Original} == Original
