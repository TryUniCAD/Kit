from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.Fields.AssertDigest import AssertDigest
from tests.Convert.Solidworks.Research.Curve.Fields.AssertLoadSnap import AssertLoadSnap


# selected loads and linked seeds need separate admission and exact source fingerprints
def AssertLoadUse(
    UsageData: dict[str, object],
    Streams: dict[str, dict[str, object]],
    StreamName: str,
    IsLinked: bool,
) -> set[str]:
    MainLoad = CastValue(dict[str, object], UsageData["load"])
    Dependencies = CastValue(list[dict[str, object]], UsageData["dependencies"])
    assert MainLoad["role"] == "field_inventory"
    assert MainLoad["requested_stream"] == StreamName
    assert len(Dependencies) == (1 if IsLinked else 0)
    SourceNames = AssertLoadSnap(MainLoad)
    for Snapshot in Dependencies:
        SourceNames.update(AssertLoadSnap(Snapshot))
        assert Snapshot["role"] == "linked_map_seed"
        assert Snapshot["requested_stream"] == "Contents/Config-0"
        assert Snapshot["tail"] == 0
        assert Snapshot["bytes"] == Streams["Contents/Config-0"]["bytes"]
        assert (
            AssertDigest(Snapshot["sha256"]) == Streams["Contents/Config-0"]["sha256"]
        )
    return SourceNames
