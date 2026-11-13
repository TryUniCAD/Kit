from __future__ import annotations

from typing import NamedTuple

from tools.TestShards.PhaseReport import PhaseReport


# finished state separates complete shard sessions from logs cut short by a crash or timeout
class ShardLog(NamedTuple):
    Phases: tuple[PhaseReport, ...]
    Finished: bool
