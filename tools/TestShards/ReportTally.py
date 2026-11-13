from __future__ import annotations

from collections import Counter
from typing import NamedTuple


# merged shard results keep timing outcomes and execution counts keyed by node id
class ReportTally(NamedTuple):
    Durations: dict[str, float]
    Outcomes: dict[str, str]
    SetupCounts: Counter[str]
    Unfinished: int
