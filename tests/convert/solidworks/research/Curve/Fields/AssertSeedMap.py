from __future__ import annotations

from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.Fields.AssertDocument import AssertDocument
from tests.convert.solidworks.research.Curve.Fields.AssertInteger import AssertInteger


# linked inventories must preserve the same seeded identities across both retained document graphs
def AssertSeedMap(
    Document: dict[str, object],
    Dependencies: list[dict[str, object]],
    Nodes: dict[str, dict[str, object]],
    IsLinked: bool,
) -> list[dict[str, object]]:
    if not IsLinked:
        assert Dependencies == []
        return []
    assert len(Dependencies) == 1
    SeedData = Dependencies[0]
    assert SeedData["name"] == "Contents/Config-0"
    SeedDoc = CastValue(dict[str, object], SeedData["document"])
    Roots = AssertDocument(SeedDoc, Nodes, "Contents/Config-0")
    assert AssertInteger(Document["map_base"]) == AssertInteger(SeedDoc["map_count"])
    MainRows = {
        AssertInteger(Entry["index"]): Entry
        for Entry in CastValue(list[dict[str, object]], Document["archive_map"])
    }
    for Entry in CastValue(list[dict[str, object]], SeedDoc["archive_map"]):
        Index = AssertInteger(Entry["index"])
        MainEntry = MainRows[Index]
        assert MainEntry["kind"] == Entry["kind"]
        assert CastValue(dict[str, object], MainEntry["value"])["target_id"] == (
            CastValue(dict[str, object], Entry["value"])["target_id"]
        )
    return Roots
