from hashlib import sha256 as HashBytes


# the checked source and prepared artifact must preserve the direction of each driver
def VerifyPlan(Evidence: dict[str, object], Prepared: bytes) -> None:
    assert Evidence["source_sha256"] == (
        "db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357"
    )
    assert Evidence["owner_span"] == ["Contents/Config-0-ResolvedFeatures", 5578, 6437]
    assert Evidence["prepared_sha256"] == HashBytes(Prepared).hexdigest()
    assert Evidence["source_operation"] == "join"
    NativeOwners = Evidence["original_native_features_outside_projection"]
    assert isinstance(NativeOwners, list) and len(NativeOwners) == 25
    Logical = Evidence["logical"]
    assert isinstance(Logical, dict)
    assert Logical["width"][-2:] == [[0, 3], 40.0]
    assert Logical["height"][-2:] == [[0, 2], 20.0]
    assert Logical["depth_mm"] == 10.0
    assert Logical["origin"] == "sldprt:sketch:26:native:6451"
    Relations = Logical["ordered_solver_relations"]
    assert len(Relations) == 7
    Prefix = "sldprt:sketch:26:profile:0:edge:"
    assert [(RowValue[1], RowValue[2]) for RowValue in Relations[:4]] == [
        (KindValue, [[Prefix + str(IndexValue), ""]])
        for IndexValue, KindValue in enumerate(
            ("horizontal", "vertical", "horizontal", "vertical")
        )
    ]
    assert Relations[4][2] == [[Prefix + "3", "end"], [Prefix + "3", "start"]]
    assert Relations[5][2] == [[Prefix + "0", "start"], [Prefix + "0", "end"]]
    assert Relations[6][2] == [[Logical["origin"], ""], [Prefix + "0", "start"]]
    assert b"$bytes" not in Prepared and b"NativeFeatureDefinition" not in Prepared
