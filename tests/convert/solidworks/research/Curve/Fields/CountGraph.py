from __future__ import annotations

from collections import Counter as CountValues
from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.Fields.AssertValue import AssertValue


# inventory counts must account for every retained value and unresolved reference occurrence
def CountGraph(
    Report: dict[str, object],
    Values: list[dict[str, object]],
    Nodes: dict[str, dict[str, object]],
    Streams: dict[str, dict[str, object]],
) -> dict[str, int]:
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
    return dict(Counts)
