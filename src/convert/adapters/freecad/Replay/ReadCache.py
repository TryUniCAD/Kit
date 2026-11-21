from __future__ import annotations

from pathlib import Path as FilePath
from typing import TypeAlias

from interchange.document.Models.DocumentModel import CadDocument

# each export distinguishes archive identity and both historical reconstruction modes
KReplayReadCache: TypeAlias = dict[
    tuple[FilePath | None, str, str, bool, bool], CadDocument
]
