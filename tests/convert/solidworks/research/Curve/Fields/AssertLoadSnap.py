from __future__ import annotations

from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.AssertSnapshot import AssertSnapshot


# complete load snapshots must preserve every schema call and successful raw field observation
def AssertLoadSnap(Snapshot: dict[str, object]) -> set[str]:
    AssertSnapshot(Snapshot)
    assert Snapshot["direction"] == "load"
    Calls = CastValue(list[dict[str, object]], Snapshot["schema_calls"])
    UsedSchemas = CastValue(list[str], Snapshot["used_schemas"])
    SourceNames: set[str] = set()
    for CallData in Calls:
        assert CallData["schema"] in UsedSchemas
        CallCount = CallData["count"]
        assert type(CallCount) is int
        assert CallCount > 0
        SourceNames.update(CastValue(list[str], CallData["source_streams"]))
    RawRecords = CastValue(list[dict[str, object]], Snapshot["raw_operations"])
    for RawRecord in RawRecords:
        assert RawRecord["completed"] is True
        assert RawRecord["observed_length"] == RawRecord["declared_length"]
    return SourceNames
