from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


# file-driven integration checks require receipts from a complete CLI process
def ReadDimensionEvidence(Root: FilePath, Source: FilePath, Run: FilePath) -> dict:
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(Root),
            "solidworks",
            "--input",
            str(Source),
            "--directory",
            str(Run),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stderr
    return LoadJson((Run / "Input-dimension-evidence.json").read_bytes())


# a held out cut must recover both configuration streams before claiming its measured dimensions
def CheckCutFields(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Source = next(
        (Root / "re/automation/PairedCaptures/P04").glob(
            "solidworks-*/*edit-cut_height_mm-10.SLDPRT"
        )
    )
    Evidence = ReadDimensionEvidence(Root, Source, TmpPath / "run")
    assert Evidence["status"] == "held_out_dimensions_match"
    assert Evidence["held_out_recipes"] == ["P04"]
    assert all(Row["recipe"] != "P04" for Row in Evidence["training"])
    assert len(Evidence["predictions"]) == Evidence["measured_count"] == 8
    Records = Evidence["discovered_dimension_records"]
    assert Records["cut_height_mm"][0]["stream"] == "Contents/Config-0"
    assert Records["cut_height_mm"][0]["system_value"] == 0.01
    assert Records["cut_depth_mm"][0]["stream"] == "Contents/Config-0-ResolvedFeatures"
    Equations = {Row["target"]: Row for Row in Evidence["equations"]}
    Left = Equations["cut_left_mm@CutSketch"]
    Bottom = Equations["cut_bottom_mm@CutSketch"]
    assert Left["status"] == "independently_varied_and_held_out"
    assert (
        Bottom["status"] == "saved_expression_replayed"
        and Bottom["vendor_edit_matches"]
    )
    assert Bottom["predicted_system_value"] == 0.005
    assert Bottom["candidate_operations"] == [["-", 2]]
    assert Bottom["manager_count"] == Bottom["scanned_count"] == 2
    assert Evidence["input_sha256"] not in Bottom["training_sha256"]


# repeated sketch dimensions require separate native count handles for the two pattern families
def CheckPatternCounts(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Source = next((Root / "re/solidworks/examples").glob("*/BLOQUE V8.SLDPRT"))
    Evidence = ReadDimensionEvidence(Root, Source, TmpPath / "run")
    Counts = Evidence["keyword_evidence"]["pattern_counts"]
    assert sorted((Row["pattern"], Row["count"]) for Row in Counts) == [
        ("circular", 6),
        ("linear", 6),
    ]
    assert all(Row["keyword_count_matches"] for Row in Counts)
    assert all(Row["possible_integer_widths"] == [1, 2, 4] for Row in Counts)
    assert len({Row["handle_value_offset"] for Row in Counts}) == 2
