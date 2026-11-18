from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Rendering.OccColour import OccColour


# pointer presence and native colour associations require distinct retained state
@DataClass(frozen=True, slots=True)
class RenderState:
    ViewValue: ArchiveNode
    CachePresent: bool
    SavedCacheCount: int | None
    ColoursValue: tuple[OccColour, ...]

    # retained colour words cannot imply a resolved portable component appearance
    @property
    def Unprojected(self) -> tuple[str, ...]:
        return ("drawing.occurrence_colours",) if self.ColoursValue else ()
