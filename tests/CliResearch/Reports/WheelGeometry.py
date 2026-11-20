# circle and revolution evidence must bind measured geometry to distinct native owners
def VerifyWheelGeom(Dimensions, Evidence):
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
    (EditRecord,) = Evidence["next_control_edits"]
    assert (EditRecord["feature"], EditRecord["field"], EditRecord["unit"]) == (
        "MatrizC2",
        "D3",
        "rad",
    )
    assert abs(EditRecord["suggested_system_value"] - 3.141592653589793) < 1e-12
