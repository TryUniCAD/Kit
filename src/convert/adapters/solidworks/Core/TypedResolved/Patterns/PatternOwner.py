from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternDatum import (
    PatternDatum,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternDim import (
    PatternDim,
)


# a neutral feature needs one verified seed direction driver set and surviving atom
@DataClass(frozen=True, slots=True)
class PatternOwner:
    NodeValue: ArchiveNode
    SeedValue: ArchiveNode
    DatumValue: PatternDatum
    DriversValue: tuple[PatternDim, ...]
    AtomsValue: tuple[int, ...]
    OutputValue: ArchiveNode
