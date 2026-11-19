from __future__ import annotations

from pathlib import Path as FilePath

from interchange.document.Models.DocumentModel import CadDocument

# each export retains complete parses by source root path archive hash and sketch profile
type ReplayReadCache = dict[tuple[FilePath | None, str, str, bool], CadDocument]
