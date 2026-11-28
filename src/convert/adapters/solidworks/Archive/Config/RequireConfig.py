from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the complete ordinary part profile requires the same concrete class as its physical start
def RequireConfig(
    NodeValue: ArchiveNode | None, *, AssemblyValue: bool = False
) -> ArchiveNode:
    ExpectedValue = RuntimeClass("moAssembly_c", 1) if AssemblyValue else KPartRoot
    if NodeValue is None or NodeValue.ClassValue != ExpectedValue:
        KindValue = "assembly" if AssemblyValue else "part"
        raise BodyUnsupported(
            f"ordinary configuration requires a current {KindValue} root"
        )
    return NodeValue
