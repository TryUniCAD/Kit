from __future__ import annotations

from typing import NamedTuple


# each pytest phase report carries the identity timing and outcome needed for verification
class PhaseReport(NamedTuple):
    TestId: str
    Phase: str
    Outcome: str
    Seconds: float
