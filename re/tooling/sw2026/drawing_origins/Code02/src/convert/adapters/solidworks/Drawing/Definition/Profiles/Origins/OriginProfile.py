from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Profiles.Origins.OriginChild import (
    OriginChild,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.ProfileDisplay import (
    ProfileDisplay,
)


@DataClass(frozen=True, slots=True)
class OriginProfile:
    DisplayValue: ProfileDisplay
    ChildValue: OriginChild
    ConfigurationValue: ArchiveNode
    ProfileValue: ArchiveNode
    SketchValue: ArchiveNode
    NativeId: int
    CreatedAt: int
