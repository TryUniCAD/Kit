from __future__ import annotations

from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.Fields.AssertDocument import AssertDocument
from tests.convert.solidworks.research.Curve.Fields.AssertNode import AssertNode
from tests.convert.solidworks.research.Curve.Fields.AssertReachable import (
    AssertReachable,
)
from tests.convert.solidworks.research.Curve.Fields.AssertSeedMap import AssertSeedMap
from tests.convert.solidworks.research.Curve.Fields.CountGraph import CountGraph


# real decoded graphs need complete reachable identities across both selected and seeded documents
def AssertGraph(
    Report: dict[str, object],
    Streams: dict[str, dict[str, object]],
    StreamName: str,
    IsLinked: bool,
) -> dict[str, int]:
    NodeRows = CastValue(list[dict[str, object]], Report["nodes"])
    assert all(
        isinstance(NodeData["id"], str) and NodeData["id"] for NodeData in NodeRows
    )
    Nodes = {CastValue(str, NodeData["id"]): NodeData for NodeData in NodeRows}
    assert len(Nodes) == len(NodeRows) == Report["node_count"]
    assert Nodes
    Document = CastValue(dict[str, object], Report["document"])
    Roots = AssertDocument(Document, Nodes, StreamName)
    Dependencies = CastValue(list[dict[str, object]], Report["dependencies"])
    Roots.extend(AssertSeedMap(Document, Dependencies, Nodes, IsLinked))
    NodeValues = {
        NodeId: AssertNode(NodeData, Nodes, Streams)
        for NodeId, NodeData in Nodes.items()
    }
    Values = [*Roots]
    for Children in NodeValues.values():
        Values.extend(Children)
    Counts = CountGraph(Report, Values, Nodes, Streams)
    AssertReachable(Roots, NodeValues, Nodes)
    if StreamName == "Contents/Config-0":
        assert all(
            Counts.get(KindName, 0) > 0 for KindName in ("int", "float", "bytes", "str")
        )
    return Counts
