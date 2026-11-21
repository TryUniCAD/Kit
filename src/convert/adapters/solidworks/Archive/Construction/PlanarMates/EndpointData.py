from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# derived endpoint state keeps semantic plane geometry distinct from serialized reference wrapper caches
@DataClass(frozen=True, slots=True)
class EndpointData:
    ReferenceValue: ArchiveNode
    FrameValue: PlaneFrame
    PlacementValue: Mapping[str, object]
    BordersValue: tuple[float, float, float, float]
    ConfigId: int
    UpdateValue: int
    DatumId: int
