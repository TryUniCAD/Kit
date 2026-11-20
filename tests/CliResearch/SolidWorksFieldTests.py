from tests.CliResearch.Reports.WheelDimensions import VerifyWheelDims
from tests.CliResearch.Reports.WheelOwnership import VerifyOwnership
from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


# file driven integration checks require receipts from a complete cli process
def ReadDimEvidence(RootPath: FilePath, Source: FilePath, RunPath: FilePath) -> dict:
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "solidworks",
            "--input",
            str(Source),
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
    return LoadJson((RunPath / "Input-dimension-evidence.json").read_bytes())


# a held out cut must recover both configuration streams before claiming its measured dimensions
def CheckCutFields(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Source = next(
        (RootPath / "re/automation/PairedCaptures/P04").glob(
            "solidworks-*/*edit-cut_height_mm-10.SLDPRT"
        )
    )
    Evidence = ReadDimEvidence(RootPath, Source, TmpPath / "run")
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
    LeftValue = Equations["cut_left_mm@CutSketch"]
    Bottom = Equations["cut_bottom_mm@CutSketch"]
    assert LeftValue["status"] == "same_family_operands_varied"
    assert (
        Bottom["status"] == "saved_expression_replayed"
        and Bottom["vendor_edit_matches"]
    )
    assert Bottom["predicted_system_value"] == 0.005
    assert Bottom["candidate_operations"] == [["-", 2]]
    assert Bottom["manager_count"] == Bottom["scanned_count"] == 2
    assert Evidence["input_sha256"] not in Bottom["training_sha256"]


# repeated sketch dimensions require separate native count handles for the two pattern families
def CheckCounts(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Source = next((RootPath / "re/solidworks/examples").glob("*/BLOQUE V8.SLDPRT"))
    RunPath = TmpPath / "run"
    Evidence = ReadDimEvidence(RootPath, Source, RunPath)
    CountRule = Evidence["keyword_evidence"]["pattern_count_rule"]
    assert CountRule["held_out_sha256"] == Evidence["input_sha256"]
    assert CountRule["samples"] == CountRule["candidates"] == []
    assert Evidence["keyword_evidence"]["pattern_counts"] == []
    Document = LoadJson((RunPath / "Input-strict.json").read_bytes())["document"]
    Counts = [
        Parameter
        for Parameter in Document["parameters"]["$tuple"]
        if Parameter["attributes"].get("dimension_kind") == "sketch_pattern_count"
    ]
    assert Counts
    CountIds = {Parameter["id"] for Parameter in Counts}
    Sketches = Document["sketches"]["$tuple"]
    assert CountIds <= {
        ParamId for Sketch in Sketches for ParamId in Sketch["parameter_ids"]["$tuple"]
    }
    for Parameter in Counts:
        assert (
            Parameter["value"]["kind"]["value"],
            Parameter["value"]["unit"],
            Parameter["value"]["value"],
        ) == ("integer", "", int(Parameter["attributes"]["source_text"]))
        assert Parameter["attributes"]["native_value"] is None
        assert Parameter["attributes"]["native_unit"] is None
    assert not any(
        Constraint["parameter_id"] in CountIds
        and Constraint["kind"] in {"distance", "distance_x", "distance_y"}
        for Sketch in Sketches
        for Constraint in Sketch["constraints"]["$tuple"]
    )


# reserved gear data cannot establish pattern count or extrusion depth rules
def CheckCountCopy(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Source = next(
        (RootPath / "re/solidworks/examples").glob("*/ENGRANE ARBOL DE LEVAS.SLDPRT")
    )
    Evidence = ReadDimEvidence(RootPath, Source, TmpPath / "run")
    CountRule = Evidence["keyword_evidence"]["feature_pattern_evidence"]
    assert CountRule["samples"] == CountRule["candidates"] == CountRule["counts"] == []
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
def CheckWheelAngle(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Source = next(
        (RootPath / "re/solidworks/examples").glob("*/RUEDA DE TURBINA.SLDPRT")
    )
    RunPath = TmpPath / "run"
    Evidence = ReadDimEvidence(RootPath, Source, RunPath)
    Fields = Evidence["discovered_feature_fields"]
    assert not Evidence["input_eligible_for_discovery"]
    assert Fields["rules"] == Fields["predictions"] == []
    Document = LoadJson((RunPath / "Input-strict.json").read_bytes())["document"]
    Parameters = {Record["id"]: Record for Record in Document["parameters"]["$tuple"]}
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
    VerifyOwnership(RunPath)
    VerifyWheelDims(RunPath, Evidence, Document)


# reopened rectangle edits challenge the byte correspondence across two independently saved streams
def CheckSingleDim(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Source = next(
        (RootPath / "re/automation/PairedCaptures/P01").glob(
            "solidworks-*/*baseline-a.SLDPRT"
        )
    )
    Evidence = ReadDimEvidence(RootPath, Source, TmpPath / "run")
    Pairs = Evidence["discovered_feature_fields"]["single_dimension_comparisons"]
    assert Evidence["input_eligible_for_discovery"]
    assert {
        (PairValue["key"][1], PairValue["input_value"], PairValue["control_value"])
        for PairValue in Pairs
    } == {("width_mm", 0.04, 0.041), ("height_mm", 0.02, 0.023)}
    assert all(
        PairValue["input_reopen"]["matches"] and PairValue["control_reopen"]["matches"]
        for PairValue in Pairs
    )


# a complete part should produce the same reader without needing a manually extracted native stream
def CheckPartReader(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    PartPath = next(
        (RootPath / "re/automation/PairedCaptures/P05").glob(
            "solidworks-*/*edit-angle_deg-90.SLDPRT"
        )
    )
    RunPath = TmpPath / "run"
    ReadDimEvidence(RootPath, PartPath, RunPath)
    Evidence = LoadJson((RunPath / "Input-scalar-streams.json").read_bytes())
    Records = Evidence["members"]["Contents/Config-0-ResolvedFeatures"]["records"]
    Angle = next(Record for Record in Records if Record["name"] == "angle_deg")
    assert abs(Angle["value"] - 1.5707963267948966) < 1e-14
    Patch = LoadJson((RunPath / "Input-scalar-stream-reader.json").read_bytes())
    assert Patch["input_sha256"] == Evidence["input_sha256"]
    assert set(Patch["verified_members"]) == set(Evidence["members"])
    assert (RunPath / "NamedScalarReader.patch").is_file()
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
def CheckInchReader(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    PartPath = next(
        (RootPath / "re/automation/PairedCaptures/P02").glob(
            "solidworks-*/*units-inch.SLDPRT"
        )
    )
    RunPath = TmpPath / "run"
    ReadDimEvidence(RootPath, PartPath, RunPath)
    Evidence = LoadJson((RunPath / "Input-scalar-streams.json").read_bytes())
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
    RootPath = ResearchRoot()
    Source = next(
        (RootPath / "re/automation/PairedCaptures/P04").glob(
            "solidworks-*/*edit-cut_width_mm-12.SLDPRT"
        )
    )
    Evidence = ReadDimEvidence(RootPath, Source, TmpPath / "run")
    (Bottom,) = [
        Record
        for Record in Evidence["equations"]
        if Record["target"] == "cut_bottom_mm@CutSketch"
    ]
    assert Bottom["status"] == "same_family_operands_varied"
    assert Bottom["candidate_operations"] == [["-", 2]]
    assert Bottom["vendor_edit_matches"] and Bottom["predicted_system_value"] == 0.006
    assert Evidence["input_sha256"] not in Bottom["training_sha256"]
