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
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetInput import SheetInput
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetNames import SheetNames


# a fresh drawing root requires complete neutral intent before any native ownership or identifier allocation begins
@DataClass(frozen=True, slots=True)
class DrawBuild:
    NameValue: str
    SheetValue: SheetInput
    SheetNames: SheetNames
    FolderValue: DrawFolders
    StyleValue: StyleInput
    UnitValue: UnitInput
    TargetValue: FeatureTarget
    CreatedAt: int
    BlockValue: UuidValue
    AutoLink: bool
