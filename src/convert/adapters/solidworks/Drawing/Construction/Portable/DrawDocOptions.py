from dataclasses import dataclass as DataClass
from uuid import UUID as UuidValue

from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Drawing.Construction.Model.DrawFolders import (
    DrawFolders,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetNames import SheetNames


# neutral drawing geometry needs explicit native presentation and provenance choices without opaque source document state
@DataClass(frozen=True, slots=True)
class DrawDocOptions:
    NameValue: str
    PropertyView: str
    SheetNames: SheetNames
    FolderValue: DrawFolders
    StyleValue: StyleInput
    UnitValue: UnitInput
    TargetValue: FeatureTarget
    CreatedAt: int
    BlockValue: UuidValue
    AutoLink: bool
