from tests.Convert.Solidworks.Configuration.ReadMemberCase import ReadMemberCase

# the native inputs store distinct relation settings and distinct color owner states
KMemberCases: tuple[
    tuple[str, int, int, list[str | int] | None, dict[str, object] | None, int], ...
] = (
    ("ladder", 60, 1, ["moFeatColorTab_c", 0, 96], {"items": [], "n": 0}, 97),
    ("concave", 53, 0, None, None, 90),
)

# each typed relation body carries the same complete empty member and cache records
KRelFields: dict[str, object] = {
    "f10": {"items": [], "n": 0},
    "f170": "",
    "f178": 0,
    "f180": 0,
    "f1b0": -1,
    "f1c0": [],
    "f58": {"items": [], "n": 0},
    "fa0": {"items": [], "n": 0},
    "ff4": -1,
    "n1c0": 0,
}


# the two disclosed parts retain their complete members and map handoffs
def TestMemberReads() -> None:
    for (
        NameValue,
        RelIndex,
        OrderValue,
        ColorClass,
        ColorFields,
        ColorCounter,
    ) in KMemberCases:
        RelValue, ColorValue, Refusals = ReadMemberCase(NameValue)
        assert RelValue["class"] == ["moRelMgr_c", 1, RelIndex]
        assert RelValue["map_counter"] == RelIndex + 1
        assert RelValue["bytes"] == 50
        assert RelValue["fields"] == {**KRelFields, "f150": OrderValue}
        assert ColorValue["class"] == ColorClass
        assert ColorValue["fields"] == ColorFields
        assert ColorValue["map_counter"] == ColorCounter
        assert ColorValue["bytes"] == (2 if ColorClass is None else 26)
        assert ColorValue["inherited_slots"] == [RelIndex - 1, RelIndex]
        assert Refusals == [
            "relation_truncated",
            "color_trailing",
            "wrong_owner",
            "version",
            "null_relation",
            "prior_relation_object",
        ]
