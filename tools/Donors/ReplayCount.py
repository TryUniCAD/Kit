from __future__ import annotations

from dataclasses import dataclass as DataClass


@DataClass(frozen=True, order=True, slots=True)
class ReplayCount:
    RootPath: str
    RuleCode: str
    CountValue: int
