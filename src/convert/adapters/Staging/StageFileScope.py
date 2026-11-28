from contextlib import contextmanager as ContextManager
from contextvars import ContextVar
from pathlib import Path as FilePath
from collections.abc import Iterator

# a staged writer can attest the final requested filesystem entry without trusting a caller option
KStageFileScope: ContextVar[tuple[FilePath, FilePath] | None] = ContextVar(
    "kit_staged_file_scope", default=None
)


# stage ownership exists only during the actual checked writer invocation
@ContextManager
def StageFileScope(StagedPath: FilePath, FinalPath: FilePath) -> Iterator[None]:
    TokenValue = KStageFileScope.set((StagedPath, FinalPath))
    try:
        yield
    finally:
        KStageFileScope.reset(TokenValue)


# the direct writer treats its actual path as final unless the current transaction owns it
def GetStagedFinal(OutputPath: FilePath) -> FilePath:
    StageValue = KStageFileScope.get()
    if StageValue is not None and OutputPath == StageValue[0]:
        return StageValue[1]
    return OutputPath
