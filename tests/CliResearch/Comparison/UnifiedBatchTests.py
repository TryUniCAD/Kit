from hashlib import sha256 as HashBytes
from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.Comparison.UnifiedFixtures import MakeInputs
from tests.CliResearch.Comparison.UnifiedReport import CheckPairProof
from tests.CliResearch.ResearchClient import ResearchCli


# the command must publish the selected original only while retaining all batch outcomes
def CheckUnified(TmpPath: FilePath) -> None:
    Original = MakeInputs(TmpPath, IncludeIssues=True)
    Reply = ResearchCli(
        TmpPath, "compare", "SolidWorks", "Fusion", "--unit", "mm", "-o", "Output"
    )
    assert Reply.returncode == 1, Reply.stderr + Reply.stdout
    Output = TmpPath / "Output"
    Summary = DecodeJson((Output / "summary.json").read_bytes())
    assert Summary["exit_code"] == 1
    assert Summary["pair_count"] == 4
    PairRows = Summary["pairs"]
    assert [(PairRow["id"], PairRow["status"]) for PairRow in PairRows] == [
        ("AEqual.json", "equal_observed_graph"),
        ("BChanged.json", "different"),
        ("CUnresolved.json", "unresolved"),
        ("DMissing.json", "missing_input"),
    ]
    assert Summary["semantic_qualification"] == "unverified"
    assert Summary["native_acceptance"] == "not_established"
    assert Summary["unified"]["policy"] == "exact_equal_observed_graph"
    assert Summary["unified"]["count"] == 1
    LeftBytes = Original[TmpPath / "SolidWorks" / "AEqual.json"]
    assert LeftBytes != Original[TmpPath / "Fusion" / "AEqual.json"]
    assert PairRows[0]["unified"] == {
        "side": "left",
        "path": "unified/0000.json",
        "sha256": HashBytes(LeftBytes).hexdigest(),
        "size_bytes": len(LeftBytes),
        "geometry_unit": "mm",
    }
    assert all(PairRow["unified"] is None for PairRow in PairRows[1:])
    Published = Output / "unified" / "0000.json"
    assert list(Published.parent.iterdir()) == [Published]
    assert Published.read_bytes() == LeftBytes
    CheckPairProof(Output, PairRows, Original)
    assert {InputPath: InputPath.read_bytes() for InputPath in Original} == Original
