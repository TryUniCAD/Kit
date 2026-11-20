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
    assert {Record["recipe"] for Record in Evidence["training"]} == {"P01", "P03"}
    assert len(Evidence["predictions"]) == Evidence["measured_count"] == 8
    Records = Evidence["discovered_dimension_records"]
    assert Records["cut_height_mm"][0]["stream"] == "Contents/Config-0"
    assert Records["cut_height_mm"][0]["system_value"] == 0.01
    assert Records["cut_depth_mm"][0]["stream"] == "Contents/Config-0-ResolvedFeatures"
    DepthEvidence = Evidence["keyword_evidence"]["extrusion_depth_evidence"]
    assert {Record["boundary"] for Record in DepthEvidence["rules"]} == {
        "stream_end",
        "next_feature",
    }
    assert {
        (Record["name"], Record["offset"])
        for Record in DepthEvidence["predictions"]
        if Record["reader_span_matches"]
    } == {("depth_mm", 8478), ("cut_depth_mm", 15331)}
    Equations = {Record["target"]: Record for Record in Evidence["equations"]}
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
    Depths = [Record for Record in Dimensions if Record["display_text"] == "3.5"]
    assert {(Record["feature_id"], Record["status"]) for Record in Depths} == {
        (89, "ambiguous"),
        (96, "ambiguous"),
    }
    Radial = [
        Record for Record in Dimensions if Record["status"] == "paired_radial_dimension"
    ]
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
    Parameters = {entry["id"]: entry for entry in Doc["parameters"]["$tuple"]}
    for Owner in (65, 257):
        Count = Parameters[f"sldprt:parameter:{Owner}:D1"]
        assert (
            Count["value"]["kind"]["value"],
            Count["value"]["unit"],
            Count["value"]["value"],
        ) == ("integer", "", 11)
        assert Count["attributes"]["native_value"] is None
    Angle = Parameters["sldprt:parameter:65:D2"]
    assert (Angle["value"]["unit"], Angle["value"]["value"]) == ("deg", 32.73)
    assert (
        Angle["attributes"]["native_value"]
        is Angle["attributes"]["native_unit"]
        is None
    )
    Scalars = LoadJson((Run / "Input-scalar-streams.json").read_bytes())
    Ownership = Scalars["members"]["Contents/Config-0-ResolvedFeatures"]["ownership"]
    Patterns = [
        Record
        for Record in Ownership["records"]
        if Record["ownership_status"] == "pattern_count_hypothesis"
    ]
    assert {Record["count_hypothesis"]["feature_id"] for Record in Patterns} == {
        65,
        257,
    }
    for Record in Patterns:
        Pattern = Record["count_hypothesis"]
        assert Pattern["count"] == 11
        assert {
            Copy["offset"] - Record["offset"]
            for Copy in Pattern["matching_copies"]
            if Copy["format"] == "<d"
        } == {373, 397}
    assert Ownership["role_counts"]["display"].get("no_matching_declaration", 0) == 57
    Selected = [
        Record
        for Record in Ownership["records"]
        if Record["selected_among_display_copies"]
    ]
    assert Selected
    assert all(Record["native_trailer"]["role"] == "driving" for Record in Selected)
    Dimensions = Evidence["keyword_evidence"]["dimensions"]
    Repeated = [
        Record
        for Record in Dimensions
        if Record["display_text"] == "<MOD-DIAM>10.16"
        and Record["status"] == "verified_profile_radius"
    ]
    assert {Record["feature_id"] for Record in Repeated} == {109, 127}
    assert len({tuple(Record["verified_location"]) for Record in Repeated}) == 2
    assert all(abs(Record["radius_m"] * 2000 - 10.16) < 1e-9 for Record in Repeated)
    Passes = LoadJson((Run / "Input-reader-passes.json").read_bytes())
    assert Passes["input_sha256"] == Evidence["input_sha256"]
    assert Passes["passes"] == []
    assert Passes["stop"] == "no_verified_patch"
    assert not (Run / "Reader.patch").exists()
    Paired = [
        Record for Record in Dimensions if Record["status"] == "paired_sketch_length"
    ]
    assert {(Record["feature_id"], Record["name"]) for Record in Paired} == {
        (66, "D2"),
        (295, "D3"),
    }
    (SketchLength,) = [
        Record
        for Record in Doc["parameters"]["$tuple"]
        if Record["id"] == "sldprt:parameter:66:D2"
    ]
    assert SketchLength["value"]["value"] == 39.41420312445611
    assert SketchLength["attributes"]["source_text"] == "39.41"
    assert SketchLength["attributes"]["native_role"] == "driving"
    assert SketchLength["provenance"]["spans"]["$tuple"][0]["offset"] == 49223
    (Circle,) = [
        Record for Record in Dimensions if Record["status"] == "verified_native_radius"
    ]
    assert Circle["feature_id"] == 261
    assert (Circle["center_offset"], Circle["rim_offset"]) == (218336, 218478)
    assert Circle["verified_location"][1] == 219738
    assert abs(2 * Circle["radius_m"] - 0.01778) < 1e-12
    (ZeroField,) = [
        Record
        for Record in Dimensions
        if Record["feature_id"] == 319 and Record["name"] == "D1"
    ]
    assert ZeroField["status"] == "ambiguous"
    Revolves = [
        Record for Record in Dimensions if Record["status"] == "verified_revolve_angle"
    ]
    assert {Record["feature_id"] for Record in Revolves} == {99, 156, 192}
    assert {Record["axis_id"] for Record in Revolves} == {46}
    assert len({tuple(Record["verified_location"]) for Record in Revolves}) == 3
    assert all(len(Record["copy_offsets"]) == 2 for Record in Revolves)
    (CutDepth,) = [
        Record
        for Record in Dimensions
        if Record["feature_id"] == 174 and Record["name"] == "D1"
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
    Angle = next(Record for Record in Records if Record["name"] == "angle_deg")
    assert abs(Angle["value"] - 1.5707963267948966) < 1e-14
    Patch = LoadJson((Run / "Input-scalar-stream-reader.json").read_bytes())
    assert Patch["input_sha256"] == Evidence["input_sha256"]
    assert set(Patch["verified_members"]) == set(Evidence["members"])
    assert (Run / "NamedScalarReader.patch").is_file()
    Owners = Evidence["owner_observations"]
    assert {(Record["feature"], Record["parameter"]) for Record in Owners} == {
        ("Revolution", "angle_deg"),
        ("AnnulusProfile", "height_mm"),
        ("AnnulusProfile", "inner_radius_mm"),
        ("AnnulusProfile", "outer_radius_mm"),
    }
    assert all(Record["status"] == "native_name_and_value_match" for Record in Owners)
    Changes = Evidence["members"]["Contents/Config-0-ResolvedFeatures"][
        "paired_changes"
    ]
    assert any(
        Record["matches_measured_change"]
        and Record["native_edit"]["feature"] == "Revolution"
        and Record["parameter"] == "angle_deg"
        and abs(Record["input_value"] - 1.5707963267948966) < 1e-14
        and abs(Record["control_value"] - 6.283185307179586) < 1e-14
        for Record in Changes
    )


# a rounded inch diameter must retain its full native scalar and exact reopen measurement
def CheckRoundedDiameterReader(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Part = next(
        (Root / "re/automation/PairedCaptures/P02").glob(
            "solidworks-*/*units-inch.SLDPRT"
        )
    )
    Run = TmpPath / "run"
    ReadDimensionEvidence(Root, Part, Run)
    Evidence = LoadJson((Run / "Input-scalar-streams.json").read_bytes())
    (Record,) = Evidence["members"]["Contents/Config-0-ResolvedFeatures"]["ownership"][
        "records"
    ]
    assert Record["value"] == 0.01
    assert Record["ownership_status"] == "rounded_declaration_and_marker_agree"
    (Match,) = Record["declaration_matches"]
    assert Match["kind"] == "diameter"
    assert Match["display"] == "<MOD-DIAM>0.39"
    (Observation,) = Evidence["owner_observations"]
    assert Observation["status"] == "native_name_and_value_match"
    assert Observation["native_values"] == [Record["value"]]


# holding out a width edit leaves both independently varied heights available to infer the bottom offset
def CheckBottomEdit(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Source = next(
        (Root / "re/automation/PairedCaptures/P04").glob(
            "solidworks-*/*edit-cut_width_mm-12.SLDPRT"
        )
    )
    Evidence = ReadDimensionEvidence(Root, Source, TmpPath / "run")
    (Bottom,) = [
        entry
        for entry in Evidence["equations"]
        if entry["target"] == "cut_bottom_mm@CutSketch"
    ]
    assert Bottom["status"] == "same_family_operands_varied"
    assert Bottom["candidate_operations"] == [["-", 2]]
    assert Bottom["vendor_edit_matches"] and Bottom["predicted_system_value"] == 0.006
    assert Evidence["input_sha256"] not in Bottom["training_sha256"]
