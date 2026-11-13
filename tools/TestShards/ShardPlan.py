from __future__ import annotations

from typing import NamedTuple


# one record per runner keeps planned membership and expected load together for reporting
class ShardPlan(NamedTuple):
    Index: int
    TestIds: tuple[str, ...]
    Estimate: float
