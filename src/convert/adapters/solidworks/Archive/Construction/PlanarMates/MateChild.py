from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# each endpoint needs the actual generated child model configuration header and registered datum inventory
@DataClass(frozen=True, slots=True)
class MateChild:
    ModelValue: ArchiveNode
    HeaderValue: ArchiveNode
    ConfigValue: ArchiveNode
    FeaturesValue: tuple[ArchiveNode, ...]
