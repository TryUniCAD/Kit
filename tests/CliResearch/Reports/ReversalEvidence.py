from json import loads as LoadJson


# saved prism evidence must reject stale geometry before the generated reader is exercised
def VerifyReversal(RunPath):
    (EditRecord,) = LoadJson((RunPath / "Input-native-edits.json").read_bytes())[
        "changes"
    ]
    Geometry = EditRecord["saved_geometry"]
    assert EditRecord["field"] == "LengthFwd"
    assert Geometry["saved_stations_mm"] == [-14.0, 5.0]
    assert Geometry["embedded_stations_mm"] == [-11.0, 5.0]
    assert Geometry["saved_depths_match"] is True
    assert Geometry["embedded_depths_match"] is False
    Graph = LoadJson((RunPath / "Input-edited-graph.json").read_bytes())
    assert Graph["status"] == "candidate_matches_native_graph"
    (Update,) = Graph["updates"]
    Reader = LoadJson((RunPath / "Input-reader-patch.json").read_bytes())
    assert Reader["observed_bindings"] == {"LengthFwd": "length"}
    assert Reader["bindings"] == {"LengthFwd": "length", "LengthRev": "second_length"}
    assert {
        Field
        for Replay in Reader["control_replays"]
        for Field in Replay["definition_fields"]
    } == {"length", "second_length"}
    assert Update["parameter_id"] == "depth:forward"
    assert Update["definition_field"] == "length"
    (FeatureStep,) = (
        Feature
        for Feature in Graph["candidate"]["feature_timeline"]["$tuple"]
        if Feature["id"] == Update["feature_id"]
    )
    assert FeatureStep["definition"]["length"]["value"] == 14.0
    assert FeatureStep["definition"]["second_length"]["value"] == 5.0
    assert (
        LoadJson((RunPath / "FileStall.json").read_bytes())["focus"]
        == "edited_graph_reopen"
    )
