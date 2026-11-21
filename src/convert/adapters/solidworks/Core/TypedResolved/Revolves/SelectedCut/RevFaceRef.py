from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# physical face incidence retains its actual representation and signed owner type
@Dataclass(frozen=True, slots=True)
class RevFaceRef:
    Representation: ArchiveNode
    ExternalValue: ArchiveNode
    FeatureId: int
    IsEnd: bool
    MarkValue: int
