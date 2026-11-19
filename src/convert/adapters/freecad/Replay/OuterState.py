from __future__ import annotations

from dataclasses import dataclass as Dataclass
from pathlib import Path as FilePath

from convert.adapters.freecad.Replay.ReplayReadScope import ReplayReadScope
from interchange.document.Models.DocumentModel import CadDocument


# linked reads share reference limits and replay context within the source root
@Dataclass(slots=True)
class OuterState:
    root: FilePath
    cache: dict[FilePath, CadDocument]
    active: set[FilePath]
    FileCount: int
    TotalBytes: int
    LegacyVisibility: bool = False
    RecordReplay: bool = False
    ReplayScope: ReplayReadScope | None = None
