from collections.abc import Mapping
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# live angular ownership must remain separate from annotation placement and cached display values
@Dataclass(frozen=True, slots=True)
class RevolveAngle:
    DisplayValue: ArchiveNode
    HandleValue: ArchiveNode
    DimensionValue: ArchiveNode
    ParameterValue: ArchiveNode
    NameValue: str
    RadiansValue: float
    OwnerValue: Mapping[str, object]
