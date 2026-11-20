from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


# file driven integration checks require receipts from a complete cli process
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
    assert Evidence["status"] == "same_family_dimensions_match"
    assert Evidence["held_out_recipes"] == ["P04"]
    assert {Row["recipe"] for Row in Evidence["training"]} == {"P01", "P03"}
    assert len(Evidence["predictions"]) == Evidence["measured_count"] == 8
    Records = Evidence["discovered_dimension_records"]
    assert Records["cut_height_mm"][0]["stream"] == "Contents/Config-0"
    assert Records["cut_height_mm"][0]["system_value"] == 0.01
    assert Records["cut_depth_mm"][0]["stream"] == "Contents/Config-0-ResolvedFeatures"
    DepthEvidence = Evidence["keyword_evidence"]["extrusion_depth_evidence"]
    assert {Row["boundary"] for Row in DepthEvidence["rules"]} == {
        "stream_end",
        "next_feature",
    }
    assert {
        (Row["name"], Row["offset"])
        for Row in DepthEvidence["predictions"]
        if Row["reader_span_matches"]
    } == {("depth_mm", 8478), ("cut_depth_mm", 15331)}
    Equations = {Row["target"]: Row for Row in Evidence["equations"]}
    Left = Equations["cut_left_mm@CutSketch"]
    Bottom = Equations["cut_bottom_mm@CutSketch"]
    assert Left["status"] == "same_family_operands_varied"
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
    Rule = Evidence["keyword_evidence"]["pattern_count_rule"]
    assert Rule["held_out_sha256"] == Evidence["input_sha256"]
    assert Rule["samples"] == Rule["candidates"] == []
    assert Evidence["keyword_evidence"]["pattern_counts"] == []


# reserved gear data cannot establish pattern count or extrusion depth rules
def CheckFeatureCountCopies(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Source = next(
        (Root / "re/solidworks/examples").glob("*/ENGRANE ARBOL DE LEVAS.SLDPRT")
    )
    Evidence = ReadDimensionEvidence(Root, Source, TmpPath / "run")
    Rule = Evidence["keyword_evidence"]["feature_pattern_evidence"]
    assert Rule["samples"] == Rule["candidates"] == Rule["counts"] == []
    Dimensions = Evidence["keyword_evidence"]["dimensions"]
    Depths = [Row for Row in Dimensions if Row["display_text"] == "3.5"]
    assert {(Row["feature_id"], Row["status"]) for Row in Depths} == {
        (89, "ambiguous"),
        (96, "ambiguous"),
    }
    Radial = [Row for Row in Dimensions if Row["status"] == "paired_radial_dimension"]
    assert len(Radial) == 1
    assert Radial[0]["display_offset"] != Radial[0]["verified_location"][1]
    assert Radial[0]["display_text"] == "<MOD-DIAM>57"


# wheel measurements retain direct evidence while untrained fields stay unresolved
def CheckRoundedPatternAngle(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Source = next((Root / "re/solidworks/examples").glob("*/RUEDA DE TURBINA.SLDPRT"))
    Run = TmpPath / "run"
    Evidence = ReadDimensionEvidence(Root, Source, Run)
    Fields = Evidence["discovered_feature_fields"]
    assert not Evidence["input_eligible_for_discovery"]
    assert Fields["rules"] == Fields["predictions"] == []
    Doc = LoadJson((Run / "Input-strict.json").read_bytes())["document"]
    Dimensions = Evidence["keyword_evidence"]["dimensions"]
    Repeated = [
        Row
        for Row in Dimensions
        if Row["display_text"] == "<MOD-DIAM>10.16"
        and Row["status"] == "verified_profile_radius"
    ]
    assert {Row["feature_id"] for Row in Repeated} == {109, 127}
    assert len({tuple(Row["verified_location"]) for Row in Repeated}) == 2
    assert all(abs(Row["radius_m"] * 2000 - 10.16) < 1e-9 for Row in Repeated)
    Passes = LoadJson((Run / "Input-reader-passes.json").read_bytes())
    assert Passes["input_sha256"] == Evidence["input_sha256"]
    assert Passes["passes"] == []
    assert Passes["stop"] == "no_verified_patch"
    assert not (Run / "Reader.patch").exists()
    Paired = [Row for Row in Dimensions if Row["status"] == "paired_sketch_length"]
    assert {(Row["feature_id"], Row["name"]) for Row in Paired} == {
        (66, "D2"),
        (295, "D3"),
    }
    (SketchLength,) = [
        Row
        for Row in Doc["parameters"]["$tuple"]
        if Row["id"] == "sldprt:parameter:66:D2"
    ]
    assert SketchLength["value"]["value"] == 39.41420312445611
    assert SketchLength["attributes"]["source_text"] == "39.41"
    assert SketchLength["attributes"]["native_role"] == "driving"
    assert SketchLength["provenance"]["spans"]["$tuple"][0]["offset"] == 49223
    (Circle,) = [Row for Row in Dimensions if Row["status"] == "verified_native_radius"]
    assert Circle["feature_id"] == 261
    assert (Circle["center_offset"], Circle["rim_offset"]) == (218336, 218478)
    assert Circle["verified_location"][1] == 219738
    assert abs(2 * Circle["radius_m"] - 0.01778) < 1e-12
    (Zero,) = [
        Row for Row in Dimensions if Row["feature_id"] == 319 and Row["name"] == "D1"
    ]
    assert Zero["status"] == "ambiguous"
    Revolves = [Row for Row in Dimensions if Row["status"] == "verified_revolve_angle"]
    assert {Row["feature_id"] for Row in Revolves} == {99, 156, 192}
    assert {Row["axis_id"] for Row in Revolves} == {46}
    assert len({tuple(Row["verified_location"]) for Row in Revolves}) == 3
    assert all(len(Row["copy_offsets"]) == 2 for Row in Revolves)
    (CutDepth,) = [
        Row for Row in Dimensions if Row["feature_id"] == 174 and Row["name"] == "D1"
    ]
    assert CutDepth["status"] == "ambiguous"
    (Edit,) = Evidence["next_control_edits"]
    assert (Edit["feature"], Edit["field"], Edit["unit"]) == ("MatrizC2", "D3", "rad")
    assert abs(Edit["suggested_system_value"] - 3.141592653589793) < 1e-12


# reopened rectangle edits challenge the byte correspondence across two independently saved streams
def CheckSingleDimensionControl(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Source = next(
        (Root / "re/automation/PairedCaptures/P01").glob(
            "solidworks-*/*baseline-a.SLDPRT"
        )
    )
    Evidence = ReadDimensionEvidence(Root, Source, TmpPath / "run")
    Pairs = Evidence["discovered_feature_fields"]["single_dimension_comparisons"]
    assert Evidence["input_eligible_for_discovery"]
    assert {
        (Pair["key"][1], Pair["input_value"], Pair["control_value"]) for Pair in Pairs
    } == {("width_mm", 0.04, 0.041), ("height_mm", 0.02, 0.023)}
    assert all(
        Pair["input_reopen"]["matches"] and Pair["control_reopen"]["matches"]
        for Pair in Pairs
    )


# a complete part should produce the same reader without needing a manually extracted native stream
def CheckNativePartScalarReader(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Part = next(
        (Root / "re/automation/PairedCaptures/P05").glob(
            "solidworks-*/*edit-angle_deg-90.SLDPRT"
        )
    )
    Run = TmpPath / "run"
    ReadDimensionEvidence(Root, Part, Run)
    Evidence = LoadJson((Run / "Input-scalar-streams.json").read_bytes())
    Records = Evidence["members"]["Contents/Config-0-ResolvedFeatures"]["records"]
    Angle = next(Row for Row in Records if Row["name"] == "angle_deg")
    assert abs(Angle["value"] - 1.5707963267948966) < 1e-14
    Patch = LoadJson((Run / "Input-scalar-stream-reader.json").read_bytes())
    assert Patch["input_sha256"] == Evidence["input_sha256"]
    assert set(Patch["verified_members"]) == set(Evidence["members"])
    assert (Run / "NamedScalarReader.patch").is_file()
