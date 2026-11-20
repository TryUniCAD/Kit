from tests.Convert.Solidworks.Configuration.ReadMemberCase import ReadMemberCase

# independently authored members expose each field that crosses the read boundary
KRelFields: dict[str, object] = {
    "f10": {"items": [{"k": ["A", "relation length"], "v": 1.25}], "n": 1},
    "f150": 2,
    "f170": ["A", "ordered members"],
    "f178": -7,
    "f180": 0xFEED1234,
    "f1b0": 12,
    "f1c0": [{"o": None}, {"o": None}],
    "f58": {"items": [], "n": 0},
    "fa0": {"items": [], "n": 0},
    "ff4": -8,
    "n1c0": 2,
}


# the authored case opens a class reference and checks both repeat interpretations
def TestMemberWire() -> None:
    RelValue, ColorValue, Refusals = ReadMemberCase("authored")
    assert RelValue["class"] == ["moRelMgr_c", 1, 61]
    assert RelValue["fields"] == KRelFields
    assert RelValue["map_counter"] == 62
    assert RelValue["inherited_slots"] == [59, 60]
    assert ColorValue["class"] == ["moFeatColorTab_c", 0, 63]
    assert ColorValue["fields"] == {"n": 0x80000000, "items": []}
    assert ColorValue["map_counter"] == 64
    assert Refusals == [
        "missing_class",
        "wrong_seed_kind",
        "truncated_repeat",
        "oversized_repeat",
        "unqualified_relation_owner",
        "wrong_color_schema",
        "unqualified_color_row",
    ]


# allocating a new class for its reference would shift later configuration map aliases
def TestColorSlot() -> None:
    Original, Reused, Refusals = ReadMemberCase("color-ref")
    assert Original["class"] == ["moFeatColorTab_c", 0, 96]
    assert Original["map_counter"] == 97
    assert Reused["class"] == ["moFeatColorTab_c", 0, 97]
    assert Reused["fields"] == {"n": 0x80000000, "items": []}
    assert Reused["bytes"] == 6
    assert Reused["map_counter"] == 98
    assert Reused["inherited_slots"] == [59, 60, 95, 96]
    assert Refusals == ["color_object_slot"]
