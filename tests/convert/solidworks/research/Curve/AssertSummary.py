from __future__ import annotations

from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.AssertSnapshot import AssertSnapshot


# aggregate usage must match its complete stream phases without inventing phase fields
def AssertSummary(
    UsageData: dict[str, object], Streams: dict[str, dict[str, object]]
) -> None:
    for Direction in ("load", "store"):
        Summary = CastValue(dict[str, object], UsageData[Direction])
        assert set(Summary) == {
            "used_schemas",
            "provisional_schemas",
            "missing_schemas",
            "raw_operation_count",
        }
        UsedNames: set[str] = set()
        RawCount = 0
        for Stream in Streams.values():
            StreamUsage = CastValue(dict[str, object], Stream["schema_usage"])
            Dependencies = [
                Snapshot
                for Snapshot in CastValue(
                    list[dict[str, object]], StreamUsage["dependencies"]
                )
                if Snapshot["direction"] == Direction
            ]
            Snapshots = [
                CastValue(dict[str, object], StreamUsage[Direction]),
                *Dependencies,
            ]
            for Snapshot in Snapshots:
                AssertSnapshot(Snapshot)
                assert Snapshot["direction"] == Direction
                UsedNames.update(CastValue(list[str], Snapshot["used_schemas"]))
                RawCount += len(CastValue(list[object], Snapshot["raw_operations"]))
        assert isinstance(Summary["used_schemas"], list)
        assert Summary["used_schemas"] == sorted(UsedNames)
        assert Summary["provisional_schemas"] == Summary["missing_schemas"] == []
        assert type(Summary["raw_operation_count"]) is int
        assert Summary["raw_operation_count"] == RawCount
