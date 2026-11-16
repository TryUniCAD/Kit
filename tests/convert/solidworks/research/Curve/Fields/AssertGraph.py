from __future__ import annotations

from collections import Counter as CountValues
from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.Fields.AssertDocument import AssertDocument
from tests.convert.solidworks.research.Curve.Fields.AssertInteger import AssertInteger
from tests.convert.solidworks.research.Curve.Fields.AssertNode import AssertNode
from tests.convert.solidworks.research.Curve.Fields.AssertValue import AssertValue


# real decoded graphs need complete reachable identities across both selected and seeded documents
def AssertGraph(
    Report: dict[str, object],
    Streams: dict[str, dict[str, object]],
    StreamName: str,
    IsLinked: bool,
) -> dict[str, int]:
    NodeRows = CastValue(list[dict[str, object]], Report["nodes"])
    Nodes = {CastValue(str, NodeData["id"]): NodeData for NodeData in NodeRows}
    assert len(Nodes) == len(NodeRows) == Report["node_count"]
    assert Nodes and all(isinstance(NodeId, str) and NodeId for NodeId in Nodes)
    Document = CastValue(dict[str, object], Report["document"])
    Roots = AssertDocument(Document, Nodes, StreamName)
    Dependencies = CastValue(list[dict[str, object]], Report["dependencies"])
    if IsLinked:
        assert len(Dependencies) == 1
        SeedData = Dependencies[0]
        assert SeedData["name"] == "Contents/Config-0"
        SeedDoc = CastValue(dict[str, object], SeedData["document"])
        Roots.extend(AssertDocument(SeedDoc, Nodes, "Contents/Config-0"))
        assert AssertInteger(Document["map_base"]) == AssertInteger(
            SeedDoc["map_count"]
        )
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
    else:
        assert Dependencies == []
    NodeValues = {
        NodeId: AssertNode(NodeData, Nodes, Streams)
        for NodeId, NodeData in Nodes.items()
    }
    Values = [*Roots]
    for Children in NodeValues.values():
        Values.extend(Children)
    Counts: CountValues[str] = CountValues()
    for Value in Values:
        AssertValue(Value, Nodes, Streams)
        KindName = CastValue(str, Value["type"])
        Counts[KindName] += 1
        if KindName == "float" and Value["finite"] is False:
            Counts["nonfinite_float"] += 1
    assert Report["reference_count"] == (
        Counts["reference"] + Counts["external-object-reference"]
    )
    assert Report["unresolved_reference_count"] == Counts["external-object-reference"]
    Pending = [
        CastValue(str, Value["target_id"])
        for Value in Roots
        if Value["type"] == "reference"
    ]
    Reached: set[str] = set()
    while Pending:
        NodeId = Pending.pop()
        if NodeId in Reached:
            continue
        Reached.add(NodeId)
        Pending.extend(
            CastValue(str, Value["target_id"])
            for Value in NodeValues[NodeId]
            if Value["type"] == "reference"
        )
    assert Reached == set(Nodes)
    if StreamName == "Contents/Config-0":
        assert all(
            Counts[KindName] > 0 for KindName in ("int", "float", "bytes", "str")
        )
    return dict(Counts)
