from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.AssertSnapshot import AssertSnapshot
from tests.Convert.Solidworks.Research.Curve.AssertUsage import AssertUsage


# byte identity must include complete stream consumption and proven linked map dependencies
def AssertStream(
    Report: dict[str, object], Streams: dict[str, dict[str, object]], IsLinked: bool
) -> None:
    UsageData = CastValue(dict[str, object], Report["schema_usage"])
    AssertUsage(UsageData)
    assert (
        Report["passed"]
        is Report["identical"]
        is Report["byte_identity_passed"]
        is Report["proven_schemas"]
        is True
    )
    assert Report["tail"] == 0
    Dependencies = CastValue(list[dict[str, object]], UsageData["dependencies"])
    for Snapshot in Dependencies:
        AssertSnapshot(Snapshot)
        SeedStream = Streams[CastValue(str, Snapshot["requested_stream"])]
        assert Snapshot["direction"] == "load"
        assert Snapshot["bytes"] == SeedStream["bytes"]
        assert Snapshot["sha256"] == SeedStream["sha256"]
        assert Snapshot["tail"] == 0
    if IsLinked:
        assert CastValue(int, Report["seeded_map_count"]) > 0
        assert any(
            Snapshot["role"] == "linked_map_seed"
            and Snapshot["requested_stream"] == "Contents/Config-0"
            for Snapshot in Dependencies
        )
