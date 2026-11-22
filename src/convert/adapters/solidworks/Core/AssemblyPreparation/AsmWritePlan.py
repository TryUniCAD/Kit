from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# validated constructor inputs must remain explicit so registry admission can inspect intent before any serialization or output writes
@DataClass(frozen=True, slots=True)
class AsmWritePlan:
    ChildDocument: CadDocument
    ChildRecipe: PartBuildInput
    ChildDimensions: RectDimInput
    RootRecipe: AssemblyInput
    Occurrences: tuple[OccurrenceIn, ...]
    MatesValue: tuple[GroupMateIn, ...]
    FixedIndex: int
