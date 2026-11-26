from hashlib import sha256 as HashBytes
from json import loads as DecodeJson
from pathlib import Path as FilePath
from shutil import copyfile as CopyFile

from pytest import MonkeyPatch as PatchScope

from tests.CliResearch.Comparison.UnifiedFixtures import MakeInputs
from tests.CliResearch.ResearchClient import ResearchCli


# a publication error must survive installed command dispatch without hiding an equal comparison
def CheckCopyError(TmpPath: FilePath, MonkeyPatch: PatchScope) -> None:
    Original = MakeInputs(TmpPath, IncludeIssues=False)
    Startup = TmpPath / "Startup"
    Startup.mkdir()
    _ = CopyFile(
        FilePath(__file__).with_name("UnifiedCopyWitness.py"),
        Startup / "sitecustomize.py",
    )
    with MonkeyPatch.context() as Scope:
        Scope.setenv("PYTHONPATH", str(Startup))
        Reply = ResearchCli(
            TmpPath, "compare", "SolidWorks", "Fusion", "--unit", "mm", "-o", "Output"
        )
    assert Reply.returncode == 1, Reply.stderr + Reply.stdout
    Output = TmpPath / "Output"
    Summary = DecodeJson((Output / "summary.json").read_bytes())
    assert Summary["exit_code"] == 1
    assert Summary["outcomes"] == {"equal_observed_graph": 1}
    assert (Summary["unified"]["count"], Summary["unified"]["errors"]) == (0, 1)
    PairRow = Summary["pairs"][0]
    assert PairRow["unified"] is None and "0000.json" in PairRow["unified_error"]
    Target = Output / "unified" / "0000.json"
    assert Target.is_dir() and not list(Target.iterdir())
    assert list(Target.parent.iterdir()) == [Target]
    ReportBytes = (Output / "reports" / "0000.json").read_bytes()
    Report = DecodeJson(ReportBytes)
    assert Report["status"] == "equal_observed_graph"
    assert HashBytes(ReportBytes).hexdigest() == PairRow["report"]["sha256"]
    assert Report["input_sha256"] == PairRow["input_sha256"]
    assert {InputPath: InputPath.read_bytes() for InputPath in Original} == Original
