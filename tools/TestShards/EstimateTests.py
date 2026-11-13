from __future__ import annotations

import statistics as StatsLib
from collections.abc import Mapping, Sequence

# unknown runtimes count as one second when no collected test has any recorded history
KDefaultWeight = 1.0


# median history stands in for new tests so unseen work still spreads evenly across shards
def EstimateTests(
    TestIds: Sequence[str], Durations: Mapping[str, float]
) -> list[float]:
    KnownTimes = [Durations[TestId] for TestId in TestIds if TestId in Durations]
    Fallback = StatsLib.median(KnownTimes) if KnownTimes else KDefaultWeight
    return [Durations.get(TestId, Fallback) for TestId in TestIds]
