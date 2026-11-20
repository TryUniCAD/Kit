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
    Rule = Evidence["keyword_evidence"]["pattern_count_rule"]
    assert Rule["candidates"] == [["<d", 401]]
    assert Rule["held_out_sha256"] == Evidence["input_sha256"]
    assert all(
        Row["sha256"] != Rule["held_out_sha256"]
        and Row["stream_sha256"] != Rule["held_out_stream_sha256"]
        for Row in Rule["samples"]
    )
    assert Evidence["keyword_evidence"]["counts"]["verified_pattern_count"] == 2
    Counts = Evidence["keyword_evidence"]["pattern_counts"]
    assert sorted((Row["pattern"], Row["count"]) for Row in Counts) == [
        ("circular", 6),
        ("linear", 6),
    ]
    assert all(Row["keyword_count_matches"] for Row in Counts)
    assert all(Row["possible_integer_widths"] == [1, 2, 4] for Row in Counts)
    assert len({Row["handle_value_offset"] for Row in Counts}) == 2
    Strict = LoadJson((TmpPath / "run/Input-strict.json").read_bytes())["document"]
    Params = {Param["id"]: Param for Param in Strict["parameters"]["$tuple"]}
    for Row in Counts:
        Param = Params[f"sldprt:parameter:{Row['feature_id']}:{Row['name']}"]
        assert Param["value"]["kind"]["value"] == "integer"
        assert Param["value"]["value"] == 6
        assert Param["value"]["unit"] == ""
        assert Param["attributes"]["native_unit"] is None
        Span = Param["provenance"]["spans"]["$tuple"][0]
        assert (Span["stream"], Span["offset"], Span["length"]) == (
            Row["stream"],
            Row["handle_value_offset"],
            8,
        )


# the camshaft gear supplies an independent feature count absent from the training parts
def CheckFeatureCountCopies(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Source = next(
        (Root / "re/solidworks/examples").glob("*/ENGRANE ARBOL DE LEVAS.SLDPRT")
    )
    Evidence = ReadDimensionEvidence(Root, Source, TmpPath / "run")
    Rule = Evidence["keyword_evidence"]["feature_pattern_evidence"]
    assert Rule["candidates"] == [["<d", 373], ["<d", 397]]
    assert all(Row["sha256"] != Evidence["input_sha256"] for Row in Rule["samples"])
    assert [Row["count"] for Row in Rule["counts"]] == [36]
    assert Rule["counts"][0]["keyword_count_matches"]
    assert Rule["counts"][0]["public_reader_matches"]
    Dimensions = Evidence["keyword_evidence"]["dimensions"]
    Depths = [Row for Row in Dimensions if Row["status"] == "held_out_extrusion_depth"]
    assert len(Depths) == 2
    assert {Row["display_text"] for Row in Depths} == {"3.5"}
    assert len({tuple(Row["verified_location"]) for Row in Depths}) == 2
    Radial = [Row for Row in Dimensions if Row["status"] == "paired_radial_dimension"]
    assert len(Radial) == 1
    assert Radial[0]["display_offset"] != Radial[0]["verified_location"][1]
    assert Radial[0]["display_text"] == "<MOD-DIAM>57"
    assert all(Row["status"] != "ambiguous" for Row in Dimensions)


# the rounded wheel display needs an independent mirror and a strict reader span for its saved precision
def CheckRoundedPatternAngle(TmpPath: FilePath) -> None:
    Root = ResearchRoot()
    Source = next((Root / "re/solidworks/examples").glob("*/RUEDA DE TURBINA.SLDPRT"))
    Run = TmpPath / "run"
    Evidence = ReadDimensionEvidence(Root, Source, Run)
    Fields = Evidence["discovered_feature_fields"]
    (Prediction,) = [
        Row for Row in Fields["predictions"] if Row["display_text"] == "32.73°"
    ]
    assert Prediction["keyword_matches"]
    assert Prediction["key"] == ["CirPattern", "D2", "angle"]
    assert Prediction["copy_offsets"] == [Prediction["scalar_offset"] + 537]
    (Rule,) = [Row for Row in Fields["rules"] if Row["key"] == Prediction["key"]]
    assert all(
        Row["file_sha256"] != Fields["input_sha256"]
        and Row["stream_sha256"] != Fields["input_stream_sha256"]
        for Row in Rule["samples"]
    )
    Doc = LoadJson((Run / "Input-strict.json").read_bytes())["document"]
    (Param,) = [
        Row
        for Row in Doc["parameters"]["$tuple"]
        if Row["id"] == "sldprt:parameter:65:D2"
    ]
    assert Param["value"]["unit"] == "deg"
    assert abs(Param["value"]["value"] - 32.72727273) < 1e-9
    assert Param["attributes"]["native_value"] == Prediction["native_value"]
    assert (
        Param["provenance"]["spans"]["$tuple"][0]["offset"]
        == Prediction["scalar_offset"]
    )
    Dimensions = Evidence["keyword_evidence"]["dimensions"]
    (Angle,) = [
        Row for Row in Dimensions if Row["status"] == "verified_mirrored_dimension"
    ]
    assert Angle["verified_location"] == [
        Prediction["stream"],
        Prediction["scalar_offset"],
    ]
    Repeated = [
        Row
        for Row in Dimensions
        if Row["display_text"] == "<MOD-DIAM>10.16"
        and Row["status"] == "verified_profile_radius"
    ]
    assert {Row["feature_id"] for Row in Repeated} == {109, 127}
    assert len({tuple(Row["verified_location"]) for Row in Repeated}) == 2
    assert all(abs(Row["radius_m"] * 2000 - 10.16) < 1e-9 for Row in Repeated)
    Angles = [
        Row
        for Row in Dimensions
        if Row["status"] == "held_out_owner_anchor" and Row["name"] == "D2"
    ]
    assert {(Row["feature_id"], Row["verified_location"][1]) for Row in Angles} == {
        (178, 163267),
        (291, 242847),
    }
    assert all(Row["anchors"] == {"object_id_delta": -1} for Row in Angles)
    (Controls,) = [
        Group
        for Group in Fields["owner_anchor_controls"]
        if Group["key"] == ["Chamfer", "D2", "angle"]
    ]
    assert len({Row["value"] for Row in Controls["samples"]}) >= 2
    assert len({Row["stream_sha256"] for Row in Controls["samples"]}) >= 2
    assert all(
        Row["stream_sha256"] != Fields["input_stream_sha256"]
        for Row in Controls["samples"]
    )

    Lengths = [
        Row
        for Row in Dimensions
        if Row["status"] == "held_out_owner_anchor" and Row["name"] == "D1"
    ]
    assert {(Row["feature_id"], Row["verified_location"][1]) for Row in Lengths} == {
        (178, 161535),
        (291, 241115),
    }
    assert all(Row["anchors"] == {"object_id_delta": -2} for Row in Lengths)
    (LengthGroup,) = [
        Group
        for Group in Fields["owner_anchor_controls"]
        if Group["key"] == ["Chamfer", "D1", "length"]
    ]
    assert any(
        Row["agreement"] == "matches_display_precision"
        and Row["display_text"] == "1.91"
        for Row in LengthGroup["samples"]
    )
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
