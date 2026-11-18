from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Detailing.DetailGroup import (
    DetailGroup,
)


# retained native references need an explicit boundary before portable edge projection is available
@DataClass(frozen=True, slots=True)
class DetailMap:
    ModelValue: ArchiveNode
    GroupsValue: tuple[DetailGroup, ...]

    # preserved associations must not masquerade as resolved portable drawing edges
    @property
    def Unprojected(self) -> tuple[str, ...]:
        return ("drawing.detailing_edges",) if self.GroupsValue else ()
