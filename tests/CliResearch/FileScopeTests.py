from hashlib import file_digest as FileDigest
from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


# a renamed real input must retain its byte identity and select experiments from its decoded features
def CheckFileScope(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    SourcePath = (
        RootPath
        / "re/automation/PairedCaptures/P04/fusion-9cf53a55ea8b/P04-fusion-termination-through-all.f3d"
    )
    InputPath = TmpPath / "unknown.bin"
    _ = InputPath.write_bytes(SourcePath.read_bytes())
    RunPath = TmpPath / "run"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(InputPath),
            "--directory",
            str(RunPath),
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
    Audit = LoadJson((RunPath / "FileScope.json").read_bytes())
    with InputPath.open("rb") as Stream:
        assert Audit["source_sha256"] == FileDigest(Stream, "sha256").hexdigest()
    assert Audit["member_count"] > 0 and Audit["unattributed_stream_ranges"]
    assert "family:extrude:cut-extrude" in Audit["selected_experiments"]
    Brep = Audit["native_classes"]["classes"]["5662F619-2281-4AD9-93DC-1FCFDA1062E7"]
    assert Brep["metatypes"] == ["BrepRefMetaType"] and "rRecipe" in Brep["fields"]
    assert (
        "5662F619-2281-4AD9-93DC-1FCFDA1062E7"
        not in Audit["reader_attempts"]["strict"]["message"]
    )
    Timeline = LoadJson((RunPath / "Input-timeline.json").read_bytes())
    assert Timeline["oracle_fields_match"] is True
    assert [Feature["name"] for Feature in Timeline["components"][0]["features"]] == [
        "RectangleSketch",
        "BlindBoss",
        "CutSketch",
        "ThroughAllCut",
    ]
    Bodies = LoadJson((RunPath / "Input-body-measurements.json").read_bytes())
    assert Bodies["count_matches"]
    assert all(Bodies["bodies"]["Body1"].values())
    Changes = LoadJson((RunPath / "Input-repeat-save.json").read_bytes())
    assert Changes["status"] == "compared"
    assert len(set(Changes["controls"]) | {Audit["source_sha256"]}) == 3
    assert any(
        Field["field"] == "side1ExtentType"
        and (Field["control"], Field["input"]) == (1, 4)
        for Field in Changes["changed_after_repeat_filter"]
    )
    assert Audit["whole_file_verified"] is False
    Outcome = LoadJson((RunPath / "CatalogueResult.json").read_bytes())
    assert Outcome["status"] == "coverage_incomplete"
    assert Outcome["scopes"]["p04-through-all-body-selection"]["assessment_job"]


# equal volume pattern members require independent centroid matches through the public command
def CheckPatternBodyIdentity(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    SourcePath = (
        RootPath / "re/Fusion/LocalOracle/FeatureAuthoring/Controls/BodyRectPattern.f3d"
    )
    RunPath = TmpPath / "pattern"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(SourcePath),
            "--directory",
            str(RunPath),
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
    Report = LoadJson((RunPath / "Input-body-correspondence.json").read_bytes())
    (Witness,) = Report["witnesses"]
    assert Witness["unique_geometry_match"]
    assert Report["default_name_rules"]["status"] == "needs_distinguishing_control"
    assert Report["default_name_rules"]["next_capture"] == "RemoveFirstDefaultBody"
    assert len(Witness["matches"]) == 6
    assert {
        (Body["stored_name"], Body["collection_ordinal"], Body["vendor_name"])
        for Body in Witness["matches"]
    } == {("", Index, f"Body{Index}") for Index in range(1, 7)}


# spline records must survive serialization through the public native reader
def CheckLoftState(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    SourcePath = RootPath / "re/Fusion/LocalOracle/FeatureAuthoring/Controls/Loft.f3d"
    RunPath = TmpPath / "loft"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(SourcePath),
            "--directory",
            str(RunPath),
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
    assert (
        b"Journal.Spline.SplineNode.SplineNode"
        in (RunPath / "Input-native.json").read_bytes()
    )
    Timeline = LoadJson((RunPath / "Input-timeline.json").read_bytes())
    assert Timeline["capture_name_checks"][0]["ordered_names_match"]
    Measurement = Timeline["parameter_checks"][0]
    assert Measurement["all_names_match"] and Measurement["native_count"] == 2
    assert Measurement["fields"] == {
        Name: {"expression": True, "unit": True, "role": True, "value": True}
        for Name in ("d1", "d2")
    }
    Audit = LoadJson((RunPath / "FileScope.json").read_bytes())
    if (
        Audit["reader_attempts"]["native"].get("message")
        == "Unsupported Fusion semantic-state value"
    ):
        Evidence = LoadJson((RunPath / "Input-state-repair.json").read_bytes())
        assert Evidence["state_round_trip"] is True
        Patch = RunPath / "BrepTypes.patch"
        assert Patch.read_text() == Evidence["patch"]
        Applicable = RunProcess(
            ["git", "apply", "--check", str(Patch)],
            cwd=RootPath,
            capture_output=True,
            text=True,
        )
        assert Applicable.returncode == 0, Applicable.stderr
