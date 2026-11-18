from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Profiles.ProfileDisplay import (
    ProfileDisplay,
)


# native profile displays cannot silently become resolved portable sketch geometry
@DataClass(frozen=True, slots=True)
class ProfileSet:
    FolderValue: ArchiveNode
    ItemsValue: tuple[ProfileDisplay, ...]

    # source display references remain unprojected until their child sketch join is proved
    @property
    def Unprojected(self) -> tuple[str, ...]:
        return ("drawing.profile_displays",) if self.ItemsValue else ()
