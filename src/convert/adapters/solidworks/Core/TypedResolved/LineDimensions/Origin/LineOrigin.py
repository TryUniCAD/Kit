from collections.abc import Mapping
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# origin coincidences need actual external and local row identities plus their retained typed reference owners
@Dataclass(frozen=True, slots=True)
class LineOrigin:
    ExternalIndex: int
    LocalIndex: int
    CreationId: int
    PositionValue: tuple[float, float]
    FieldsValue: Mapping[str, object]
    RelationValue: Mapping[str, object]
    FeatureValue: ArchiveNode
    SelectionValue: ArchiveNode
    WrapperValue: ArchiveNode
    ExternalValue: ArchiveNode
    BackupValue: ArchiveNode
    OwnerValue: Mapping[str, object]
    ReferenceOwners: Mapping[str, Mapping[str, object]]
