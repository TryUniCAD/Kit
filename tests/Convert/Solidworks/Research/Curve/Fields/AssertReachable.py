from __future__ import annotations

from typing import cast as CastValue


# orphaned node records would conceal missing connections in otherwise well formed inventory output
def AssertReachable(
    Roots: list[dict[str, object]],
    NodeValues: dict[str, list[dict[str, object]]],
    Nodes: dict[str, dict[str, object]],
) -> None:
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
