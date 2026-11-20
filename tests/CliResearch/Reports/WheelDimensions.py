from tests.CliResearch.Reports.WheelGeometry import VerifyWheelGeom
from json import loads as LoadJson


# wheel dimension receipts must retain independent owners and exact spans across reader passes
def VerifyWheelDims(RunPath, Evidence, Document):
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
    Passes = LoadJson((RunPath / "Input-reader-passes.json").read_bytes())
    assert Passes["input_sha256"] == Evidence["input_sha256"]
    assert Passes["passes"] == []
    assert Passes["stop"] == "no_verified_patch"
    assert not (RunPath / "Reader.patch").exists()
    Paired = [
        Record for Record in Dimensions if Record["status"] == "paired_sketch_length"
    ]
    assert {(Record["feature_id"], Record["name"]) for Record in Paired} == {
        (66, "D2"),
        (295, "D3"),
    }
    (SketchLength,) = [
        Record
        for Record in Document["parameters"]["$tuple"]
        if Record["id"] == "sldprt:parameter:66:D2"
    ]
    assert SketchLength["value"]["value"] == 39.41420312445611
    assert SketchLength["attributes"]["source_text"] == "39.41"
    assert SketchLength["attributes"]["native_role"] == "driving"
    assert SketchLength["provenance"]["spans"]["$tuple"][0]["offset"] == 49223
    VerifyWheelGeom(Dimensions, Evidence)
