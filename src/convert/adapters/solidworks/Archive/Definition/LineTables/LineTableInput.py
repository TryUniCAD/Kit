from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Definition.LineTables.CheckLineInput import (
    CheckLineInput,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.FontBinding import (
    FontBinding,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.LinePattern import (
    LinePattern,
)


# source presentation needs semantic patterns and constructor insertions rather than native field dictionaries
@DataClass(frozen=True, slots=True)
class LineTableInput:
    PatternValues: tuple[LinePattern, ...]
    BindingValues: tuple[FontBinding, ...]

    # constructor order remains explicit while native bucket traversal is derived separately
    def __post_init__(self) -> None:
        CheckLineInput(self.PatternValues, self.BindingValues)
