from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a complete unit component binds its enclosing part while bounded records retain their frame identity
def PartScopeOwner(ContextValue: BodyContext, NodeValue: ArchiveNode) -> ArchiveNode:
    PartRoot = ContextValue.PartRootValue
    if PartRoot is not None and NodeValue.ClassValue == RuntimeClass(
        "moUnitComponent_c", 1
    ):
        return PartRoot
    return NodeValue
