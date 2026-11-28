from contextvars import ContextVar
from pathlib import Path as FilePath

# measured adapters need the registry owned stage and final pair independently of caller options
KPathStageOwner: ContextVar[tuple[FilePath, FilePath] | None] = ContextVar(
    "kit_path_stage_owner", default=None
)
