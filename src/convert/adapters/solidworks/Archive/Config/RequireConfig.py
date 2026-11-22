from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the complete ordinary part profile requires the same concrete class as its physical start
def RequireConfig(NodeValue: ArchiveNode | None) -> ArchiveNode:
    if NodeValue is None or NodeValue.ClassValue != KPartRoot:
        raise BodyUnsupported("ordinary configuration requires a current part root")
    return NodeValue
