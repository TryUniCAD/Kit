from os import DirEntry, PathLike, scandir as ScanDirectory
from types import TracebackType
from pathlib import Path as FilePath


# real entry telemetry distinguishes streaming refusal from eager traversal without replacing filesystem results
class ScanWitness:

    # the original stream must remain responsible for real directory access and entry identity
    def __init__(
        self,
        TargetRoot: FilePath,
        Counter: list[int],
        Directory: str | PathLike[str] | int = ".",
    ) -> None:
        super().__init__()
        self.Stream = ScanDirectory(Directory)
        self.Counter = Counter
        self.Observed = (
            not isinstance(Directory, int)
            and FilePath(Directory).resolve() == TargetRoot
        )

    # iteration must keep entry counting active while retaining the original stream lifecycle
    def __iter__(self) -> "ScanWitness":
        _ = iter(self.Stream)
        return self

    # counting successful real reads exposes consumption beyond the declared discovery budget
    def __next__(self) -> DirEntry[str]:
        EntryValue = next(self.Stream)
        if self.Observed:
            self.Counter[0] += 1
        return EntryValue

    # unobserved native operations must retain their original behavior rather than requiring imitation
    def __getattr__(self, Attribute: str) -> object:
        return getattr(self.Stream, Attribute)

    # entering the real context preserves the command lifecycle instead of substituting fake resources
    def __enter__(self) -> "ScanWitness":
        _ = self.Stream.__enter__()
        return self

    # native cleanup and exception handling must remain owned by the real filesystem stream
    def __exit__(
        self,
        ErrorType: type[BaseException] | None,
        ErrorValue: BaseException | None,
        Traceback: TracebackType | None,
    ) -> None:
        self.Stream.__exit__(ErrorType, ErrorValue, Traceback)
