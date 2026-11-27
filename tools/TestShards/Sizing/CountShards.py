from collections.abc import Mapping, Sequence
from math import ceil as CeilValue, isfinite as IsFinite

from tools.TestShards.EstimateTests import EstimateTests


# runtime sizing prevents slow cases from hiding behind a count only shard budget
def CountShards(
    TestIds: Sequence[str],
    Durations: Mapping[str, float],
    TargetSecs: float,
    RuntimeShards: int,
) -> int:
    if not IsFinite(TargetSecs) or TargetSecs < 0 or RuntimeShards < 1:
        raise ValueError(
            "runtime target must be finite and nonnegative with a positive shard budget"
        )
    if (
        not TestIds
        or TargetSecs == 0
        or not any(TestId in Durations for TestId in TestIds)
    ):
        return 0
    return min(
        len(TestIds),
        RuntimeShards,
        CeilValue(sum(EstimateTests(TestIds, Durations)) / TargetSecs),
    )
